# © 2016 Julien Coux (Camptocamp)
# © 2018 Forest and Biomass Romania SA
# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import _, api, models
from odoo.tools.float_utils import float_is_zero


class TrialBalanceReport(models.AbstractModel):
    _name = "report.account_financial_report.trial_balance"
    _description = "Trial Balance Report"
    _inherit = "report.account_financial_report.abstract_report"

    def _get_initial_balances_bs_ml_domain(
        self,
        account_ids,
        journal_ids,
        partner_ids,
        company_id,
        date_from,
        only_posted_moves,
        show_partner_details,
    ):
        accounts_domain = [
            ("company_id", "=", company_id),
            ("user_type_id.include_initial_balance", "=", True),
        ]
        if account_ids:
            accounts_domain += [("id", "in", account_ids)]
        domain = [("date", "<", date_from)]
        accounts = self.env["account.account"].search(accounts_domain)
        domain += [("account_id", "in", accounts.ids)]
        if company_id:
            domain += [("company_id", "=", company_id)]
        if journal_ids:
            domain += [("journal_id", "in", journal_ids)]
        if partner_ids:
            domain += [("partner_id", "in", partner_ids)]
        if only_posted_moves:
            domain += [("move_id.state", "=", "posted")]
        else:
            domain += [("move_id.state", "in", ["posted", "draft"])]
        if show_partner_details:
            domain += [("account_id.internal_type", "in", ["receivable", "payable"])]
        return domain

    def _get_initial_balances_pl_ml_domain(
        self,
        account_ids,
        journal_ids,
        partner_ids,
        company_id,
        date_from,
        only_posted_moves,
        show_partner_details,
        fy_start_date,
    ):
        accounts_domain = [
            ("company_id", "=", company_id),
            ("user_type_id.include_initial_balance", "=", False),
        ]
        if account_ids:
            accounts_domain += [("id", "in", account_ids)]
        domain = [("date", "<", date_from), ("date", ">=", fy_start_date)]
        accounts = self.env["account.account"].search(accounts_domain)
        domain += [("account_id", "in", accounts.ids)]
        if company_id:
            domain += [("company_id", "=", company_id)]
        if journal_ids:
            domain += [("journal_id", "in", journal_ids)]
        if partner_ids:
            domain += [("partner_id", "in", partner_ids)]
        if only_posted_moves:
            domain += [("move_id.state", "=", "posted")]
        else:
            domain += [("move_id.state", "in", ["posted", "draft"])]
        if show_partner_details:
            domain += [("account_id.internal_type", "in", ["receivable", "payable"])]
        return domain

    @api.model
    def _get_period_ml_domain(
        self,
        account_ids,
        journal_ids,
        partner_ids,
        company_id,
        date_to,
        date_from,
        only_posted_moves,
        show_partner_details,
    ):
        domain = [
            ("display_type", "=", False),
            ("date", ">=", date_from),
            ("date", "<=", date_to),
        ]
        if company_id:
            domain += [("company_id", "=", company_id)]
        if account_ids:
            domain += [("account_id", "in", account_ids)]
        if journal_ids:
            domain += [("journal_id", "in", journal_ids)]
        if partner_ids:
            domain += [("partner_id", "in", partner_ids)]
        if only_posted_moves:
            domain += [("move_id.state", "=", "posted")]
        else:
            domain += [("move_id.state", "in", ["posted", "draft"])]
        if show_partner_details:
            domain += [("account_id.internal_type", "in", ["receivable", "payable"])]
        return domain

    def _get_initial_balance_fy_pl_ml_domain(
        self,
        account_ids,
        journal_ids,
        partner_ids,
        company_id,
        fy_start_date,
        only_posted_moves,
        show_partner_details,
    ):
        accounts_domain = [
            ("company_id", "=", company_id),
            ("user_type_id.include_initial_balance", "=", False),
        ]
        if account_ids:
            accounts_domain += [("id", "in", account_ids)]
        domain = [("date", "<", fy_start_date)]
        accounts = self.env["account.account"].search(accounts_domain)
        domain += [("account_id", "in", accounts.ids)]
        if company_id:
            domain += [("company_id", "=", company_id)]
        if journal_ids:
            domain += [("journal_id", "in", journal_ids)]
        if partner_ids:
            domain += [("partner_id", "in", partner_ids)]
        if only_posted_moves:
            domain += [("move_id.state", "=", "posted")]
        else:
            domain += [("move_id.state", "in", ["posted", "draft"])]
        if show_partner_details:
            domain += [("account_id.internal_type", "in", ["receivable", "payable"])]
        return domain

    def _get_pl_initial_balance(
        self,
        account_ids,
        journal_ids,
        partner_ids,
        company_id,
        fy_start_date,
        only_posted_moves,
        show_partner_details,
        foreign_currency,
    ):
        domain = self._get_initial_balance_fy_pl_ml_domain(
            account_ids,
            journal_ids,
            partner_ids,
            company_id,
            fy_start_date,
            only_posted_moves,
            show_partner_details,
        )
        initial_balances = self.env["account.move.line"].read_group(
            domain=domain,
            fields=["account_id", "balance", "amount_currency"],
            groupby=["account_id"],
        )
        pl_initial_balance = 0.0
        pl_initial_currency_balance = 0.0
        for initial_balance in initial_balances:
            pl_initial_balance += initial_balance["balance"]
            if foreign_currency:
                pl_initial_currency_balance += round(
                    initial_balance["amount_currency"], 2
                )
        return pl_initial_balance, pl_initial_currency_balance

    @api.model
    def _compute_account_amount(
        self, total_amount, tb_initial_acc, tb_period_acc, foreign_currency
    ):
        for tb in tb_period_acc:
            acc_id = tb["account_id"][0]
            total_amount[acc_id] = self._prepare_total_amount(tb, foreign_currency)
            total_amount[acc_id]["credit"] = tb["credit"]
            total_amount[acc_id]["debit"] = tb["debit"]
            total_amount[acc_id]["balance"] = tb["balance"]
            total_amount[acc_id]["initial_balance"] = 0.0
        for tb in tb_initial_acc:
            acc_id = tb["account_id"]
            if acc_id not in total_amount.keys():
                total_amount[acc_id] = self._prepare_total_amount(tb, foreign_currency)
            else:
                total_amount[acc_id]["initial_balance"] = tb["balance"]
                total_amount[acc_id]["ending_balance"] += tb["balance"]
                if foreign_currency:
                    total_amount[acc_id]["initial_currency_balance"] = round(
                        tb["amount_currency"], 2
                    )
                    total_amount[acc_id]["ending_currency_balance"] += round(
                        tb["amount_currency"], 2
                    )
        return total_amount

    @api.model
    def _prepare_total_amount(self, tb, foreign_currency):
        res = {
            "credit": 0.0,
            "debit": 0.0,
            "balance": 0.0,
            "initial_balance": tb["balance"],
            "ending_balance": tb["balance"],
        }
        if foreign_currency:
            res["initial_currency_balance"] = round(tb["amount_currency"], 2)
            res["ending_currency_balance"] = round(tb["amount_currency"], 2)
        return res

    @api.model
    def _compute_acc_prt_amount(
        self, total_amount, tb, acc_id, prt_id, foreign_currency
    ):
        # Add keys to dict if not exists
        if acc_id not in total_amount:
            total_amount[acc_id] = self._prepare_total_amount(tb, foreign_currency)
        if prt_id not in total_amount[acc_id]:
            total_amount[acc_id][prt_id] = self._prepare_total_amount(
                tb, foreign_currency
            )
        else:
            # Increase balance field values
            total_amount[acc_id][prt_id]["initial_balance"] = tb["balance"]
            total_amount[acc_id][prt_id]["ending_balance"] += tb["balance"]
            if foreign_currency:
                total_amount[acc_id][prt_id]["initial_currency_balance"] = round(
                    tb["amount_currency"], 2
                )
                total_amount[acc_id][prt_id]["ending_currency_balance"] += round(
                    tb["amount_currency"], 2
                )
        return total_amount

    @api.model
    def _compute_partner_amount(
        self, total_amount, tb_initial_prt, tb_period_prt, foreign_currency
    ):
        partners_ids = set()
        partners_data = {}
        for tb in tb_period_prt:
            acc_id = tb["account_id"][0]
            prt_id = tb["partner_id"][0] if tb["partner_id"] else 0
            if prt_id not in partners_ids:
                partner_name = (
                    tb["partner_id"][1] if tb["partner_id"] else _("Missing Partner")
                )
                partners_data.update({prt_id: {"id": prt_id, "name": partner_name}})
            total_amount[acc_id][prt_id] = self._prepare_total_amount(
                tb, foreign_currency
            )
            total_amount[acc_id][prt_id]["credit"] = tb["credit"]
            total_amount[acc_id][prt_id]["debit"] = tb["debit"]
            total_amount[acc_id][prt_id]["balance"] = tb["balance"]
            total_amount[acc_id][prt_id]["initial_balance"] = 0.0
            partners_ids.add(prt_id)
        for tb in tb_initial_prt:
            acc_id = tb["account_id"][0]
            prt_id = tb["partner_id"][0] if tb["partner_id"] else 0
            if prt_id not in partners_ids:
                partner_name = (
                    tb["partner_id"][1] if tb["partner_id"] else _("Missing Partner")
                )
                partners_data.update({prt_id: {"id": prt_id, "name": partner_name}})
            total_amount = self._compute_acc_prt_amount(
                total_amount, tb, acc_id, prt_id, foreign_currency
            )
        return total_amount, partners_data

    def _remove_accounts_at_cero(self, total_amount, show_partner_details, company):
        def is_removable(d):
            rounding = company.currency_id.rounding
            return (
                float_is_zero(d["initial_balance"], precision_rounding=rounding)
                and float_is_zero(d["credit"], precision_rounding=rounding)
                and float_is_zero(d["debit"], precision_rounding=rounding)
                and float_is_zero(d["ending_balance"], precision_rounding=rounding)
            )

        accounts_to_remove = []
        for acc_id, ta_data in total_amount.items():
            if is_removable(ta_data):
                accounts_to_remove.append(acc_id)
            elif show_partner_details:
                partner_to_remove = []
                for key, value in ta_data.items():
                    # If the show_partner_details option is checked,
                    # the partner data is in the same account data dict
                    # but with the partner id as the key
                    if isinstance(key, int) and is_removable(value):
                        partner_to_remove.append(key)
                for partner_id in partner_to_remove:
                    del ta_data[partner_id]
        for account_id in accounts_to_remove:
            del total_amount[account_id]

    @api.model
    def _get_data(
        self,
        account_ids,
        journal_ids,
        partner_ids,
        company_id,
        date_to,
        date_from,
        foreign_currency,
        only_posted_moves,
        show_partner_details,
        hide_account_at_0,
        unaffected_earnings_account,
        fy_start_date,
        grouped_by,
    ):
        tb_data = {}
        accounts_domain = [("company_id", "=", company_id)]
        if account_ids:
            accounts_domain += [("id", "in", account_ids)]
            # If explicit list of accounts is provided,
            # don't include unaffected earnings account
            unaffected_earnings_account = False
        accounts = self.env["account.account"].search(accounts_domain)
        for account in accounts:
            tb_data[account.id] = self._initialize_data(foreign_currency)
            tb_data[account.id]["id"] = account.id
            tb_data[account.id]["mame"] = account.name
            if grouped_by:
                tb_data[account.id][grouped_by] = False
        initial_domain_bs = self._get_initial_balances_bs_ml_domain(
            account_ids,
            journal_ids,
            partner_ids,
            company_id,
            date_from,
            only_posted_moves,
            show_partner_details,
        )
        tb_initial_acc_bs = self.env["account.move.line"].read_group(
            domain=initial_domain_bs,
            fields=["account_id", "balance", "amount_currency"],
            groupby=["account_id"],
        )
        initial_domain_pl = self._get_initial_balances_pl_ml_domain(
            account_ids,
            journal_ids,
            partner_ids,
            company_id,
            date_from,
            only_posted_moves,
            show_partner_details,
            fy_start_date,
        )
        tb_initial_acc_pl = self.env["account.move.line"].read_group(
            domain=initial_domain_pl,
            fields=["account_id", "balance", "amount_currency"],
            groupby=["account_id"],
        )
        tb_initial_acc_rg = tb_initial_acc_bs + tb_initial_acc_pl
        for account_rg in tb_initial_acc_rg:
            a_rg_id = account_rg["account_id"][0]
            if a_rg_id in tb_data:
                tb_data[a_rg_id]["init_bal"]["balance"] += account_rg["balance"]
                if foreign_currency:
                    tb_data[a_rg_id]["init_bal"]["bal_curr"] += account_rg[
                        "amount_currency"
                    ]
        period_domain = self._get_period_ml_domain(
            account_ids,
            journal_ids,
            partner_ids,
            company_id,
            date_to,
            date_from,
            only_posted_moves,
            show_partner_details,
        )
        ml_fields = self._get_ml_fields()
        move_lines = self.env["account.move.line"].search_read(
            domain=period_domain, fields=ml_fields, order="date,move_name"
        )
        for move_line in move_lines:
            acc_id = move_line["account_id"][0]
            ml_id = move_line["id"]
            if acc_id not in tb_data.keys():
                tb_data[acc_id] = self._initialize_data(foreign_currency)
                tb_data[acc_id]["id"] = acc_id
                tb_data[acc_id]["mame"] = move_line["account_id"][1]
                if grouped_by:
                    tb_data[acc_id][grouped_by] = False
            if acc_id in accounts.ids:
                item_ids = self._prepare_ml_items(move_line, grouped_by)
                for item in item_ids:
                    item_id = item["id"]
                    if item_id not in tb_data[acc_id]:
                        if grouped_by:
                            tb_data[acc_id][grouped_by] = True
                        tb_data[acc_id][item_id] = self._initialize_data(
                            foreign_currency
                        )
                        tb_data[acc_id][item_id]["id"] = item_id
                        tb_data[acc_id][item_id]["name"] = item["name"]
                    tb_data[acc_id][item_id][ml_id] = self._get_move_line_data(
                        move_line
                    )
                    tb_data[acc_id][item_id]["fin_bal"]["credit"] += move_line["credit"]
                    tb_data[acc_id][item_id]["fin_bal"]["debit"] += move_line["debit"]
                    tb_data[acc_id][item_id]["fin_bal"]["balance"] += move_line[
                        "balance"
                    ]
                    if foreign_currency:
                        tb_data[acc_id][item_id]["fin_bal"]["bal_curr"] += move_line[
                            "amount_currency"
                        ]
            else:
                tb_data[acc_id][ml_id] = self._get_move_line_data(move_line)
            tb_data[acc_id]["fin_bal"]["credit"] += move_line["credit"]
            tb_data[acc_id]["fin_bal"]["debit"] += move_line["debit"]
            tb_data[acc_id]["fin_bal"]["balance"] += move_line["balance"]
            if foreign_currency:
                tb_data[acc_id]["fin_bal"]["bal_curr"] += move_line["amount_currency"]
        accounts_ids = list(tb_data.keys())
        unaffected_id = unaffected_earnings_account
        if unaffected_id:
            if unaffected_id not in accounts_ids:
                accounts_ids.append(unaffected_id)
                tb_data[unaffected_id] = self._initialize_data(foreign_currency)
                tb_data[unaffected_id]["id"] = unaffected_id.id
                tb_data[unaffected_id]["mame"] = unaffected_id.name
                if grouped_by:
                    tb_data[unaffected_id][grouped_by] = False

        accounts_data = self._get_accounts_data(accounts_ids)
        (
            pl_initial_balance,
            pl_initial_currency_balance,
        ) = self._get_pl_initial_balance(
            account_ids,
            journal_ids,
            partner_ids,
            company_id,
            fy_start_date,
            only_posted_moves,
            show_partner_details,
            foreign_currency,
        )
        if unaffected_id:
            tb_data[unaffected_id]["fin_bal"]["balance"] += pl_initial_balance
            if foreign_currency:
                tb_data[unaffected_id]["fin_bal"][
                    "bal_curr"
                ] += pl_initial_currency_balance
            tb_data[unaffected_id]["init_bal"]["balance"] += pl_initial_balance
            if foreign_currency:
                tb_data[unaffected_id]["init_bal"][
                    "bal_curr"
                ] += pl_initial_currency_balance
        return tb_data, accounts_data

    def _get_hierarchy_groups(self, group_ids, groups_data, foreign_currency):
        for group_id in group_ids:
            parent_id = groups_data[group_id]["parent_id"]
            while parent_id:
                if parent_id not in groups_data.keys():
                    group = self.env["account.group"].browse(parent_id)
                    groups_data[group.id] = {
                        "id": group.id,
                        "code": group.code_prefix_start,
                        "name": group.name,
                        "parent_id": group.parent_id.id,
                        "parent_path": group.parent_path,
                        "complete_code": group.complete_code,
                        "account_ids": group.compute_account_ids.ids,
                        "type": "group_type",
                        "initial_balance": 0,
                        "debit": 0,
                        "credit": 0,
                        "balance": 0,
                        "ending_balance": 0,
                    }
                    if foreign_currency:
                        groups_data[group.id].update(
                            initial_currency_balance=0,
                            ending_currency_balance=0,
                        )
                acc_keys = ["debit", "credit", "balance"]
                acc_keys += ["initial_balance", "ending_balance"]
                for acc_key in acc_keys:
                    groups_data[parent_id][acc_key] += groups_data[group_id][acc_key]
                if foreign_currency:
                    groups_data[group_id]["initial_currency_balance"] += groups_data[
                        group_id
                    ]["initial_currency_balance"]
                    groups_data[group_id]["ending_currency_balance"] += groups_data[
                        group_id
                    ]["ending_currency_balance"]
                parent_id = groups_data[parent_id]["parent_id"]
        return groups_data

    def _get_groups_data(self, accounts_data, total_amount, foreign_currency):
        accounts_ids = list(accounts_data.keys())
        accounts = self.env["account.account"].browse(accounts_ids)
        account_group_relation = {}
        for account in accounts:
            accounts_data[account.id]["complete_code"] = (
                account.group_id.complete_code + " / " + account.code
                if account.group_id.id
                else ""
            )
            if account.group_id.id:
                if account.group_id.id not in account_group_relation.keys():
                    account_group_relation.update({account.group_id.id: [account.id]})
                else:
                    account_group_relation[account.group_id.id].append(account.id)
        groups = self.env["account.group"].browse(account_group_relation.keys())
        groups_data = {}
        for group in groups:
            groups_data.update(
                {
                    group.id: {
                        "id": group.id,
                        "code": group.code_prefix_start,
                        "name": group.name,
                        "parent_id": group.parent_id.id,
                        "parent_path": group.parent_path,
                        "type": "group_type",
                        "complete_code": group.complete_code,
                        "account_ids": group.compute_account_ids.ids,
                        "initial_balance": 0.0,
                        "credit": 0.0,
                        "debit": 0.0,
                        "balance": 0.0,
                        "ending_balance": 0.0,
                    }
                }
            )
            if foreign_currency:
                groups_data[group.id]["initial_currency_balance"] = 0.0
                groups_data[group.id]["ending_currency_balance"] = 0.0
        for group_id in account_group_relation.keys():
            for account_id in account_group_relation[group_id]:
                groups_data[group_id]["initial_balance"] += total_amount[account_id][
                    "initial_balance"
                ]
                groups_data[group_id]["debit"] += total_amount[account_id]["debit"]
                groups_data[group_id]["credit"] += total_amount[account_id]["credit"]
                groups_data[group_id]["balance"] += total_amount[account_id]["balance"]
                groups_data[group_id]["ending_balance"] += total_amount[account_id][
                    "ending_balance"
                ]
                if foreign_currency:
                    groups_data[group_id]["initial_currency_balance"] += total_amount[
                        account_id
                    ]["initial_currency_balance"]
                    groups_data[group_id]["ending_currency_balance"] += total_amount[
                        account_id
                    ]["ending_currency_balance"]
        group_ids = list(groups_data.keys())
        groups_data = self._get_hierarchy_groups(
            group_ids,
            groups_data,
            foreign_currency,
        )
        return groups_data

    def _get_computed_groups_data(self, accounts_data, total_amount, foreign_currency):
        groups = self.env["account.group"].search([("id", "!=", False)])
        groups_data = {}
        for group in groups:
            len_group_code = len(group.code_prefix_start)
            groups_data.update(
                {
                    group.id: {
                        "id": group.id,
                        "code": group.code_prefix_start,
                        "name": group.name,
                        "parent_id": group.parent_id.id,
                        "parent_path": group.parent_path,
                        "type": "group_type",
                        "complete_code": group.complete_code,
                        "account_ids": group.compute_account_ids.ids,
                        "initial_balance": 0.0,
                        "credit": 0.0,
                        "debit": 0.0,
                        "balance": 0.0,
                        "ending_balance": 0.0,
                    }
                }
            )
            if foreign_currency:
                groups_data[group.id]["initial_currency_balance"] = 0.0
                groups_data[group.id]["ending_currency_balance"] = 0.0
            for account in accounts_data.values():
                if group.code_prefix_start == account["code"][:len_group_code]:
                    acc_id = account["id"]
                    group_id = group.id
                    groups_data[group_id]["initial_balance"] += total_amount[acc_id][
                        "initial_balance"
                    ]
                    groups_data[group_id]["debit"] += total_amount[acc_id]["debit"]
                    groups_data[group_id]["credit"] += total_amount[acc_id]["credit"]
                    groups_data[group_id]["balance"] += total_amount[acc_id]["balance"]
                    groups_data[group_id]["ending_balance"] += total_amount[acc_id][
                        "ending_balance"
                    ]
                    if foreign_currency:
                        groups_data[group_id][
                            "initial_currency_balance"
                        ] += total_amount[acc_id]["initial_currency_balance"]
                        groups_data[group_id][
                            "ending_currency_balance"
                        ] += total_amount[acc_id]["ending_currency_balance"]
        return groups_data

    def _create_trial_balance(
        self,
        tb_data,
        show_partner_details,
        show_hierarchy,
        foreign_currency,
        accounts_data,
        grouped_by,
        hide_account_at_0,
    ):
        trial_balance = []
        rounding = self.env.company.currency_id.rounding
        for acc_id in tb_data.keys():
            account = {}
            account.update(
                {
                    "code": accounts_data[acc_id]["code"],
                    "name": accounts_data[acc_id]["name"],
                    "type": "account",
                    "currency_id": accounts_data[acc_id]["currency_id"],
                    "centralized": accounts_data[acc_id]["centralized"],
                    "grouped_by": grouped_by,
                }
            )
            if grouped_by and not tb_data[acc_id][grouped_by]:
                account = self._create_account(account, acc_id, tb_data)
                if (
                    hide_account_at_0
                    and float_is_zero(
                        tb_data[acc_id]["init_bal"]["balance"],
                        precision_rounding=rounding,
                    )
                    and account["move_lines"] == []
                ):
                    continue
            else:
                if grouped_by:
                    account, list_grouped = self._get_list_grouped_item(
                        tb_data[acc_id],
                        account,
                        hide_account_at_0,
                        rounding,
                    )
                    account.update({"list_grouped": list_grouped})
                    if (
                        hide_account_at_0
                        and float_is_zero(
                            tb_data[acc_id]["init_bal"]["balance"],
                            precision_rounding=rounding,
                        )
                        and account["list_grouped"] == []
                    ):
                        continue
                else:
                    account = self._create_account_not_show_item(
                        account, acc_id, tb_data, grouped_by
                    )
                    if (
                        hide_account_at_0
                        and float_is_zero(
                            tb_data[acc_id]["init_bal"]["balance"],
                            precision_rounding=rounding,
                        )
                        and account["move_lines"] == []
                    ):
                        continue
            trial_balance += [account]
        return trial_balance

    def _get_report_values(self, docids, data):
        show_partner_details = data["show_partner_details"]
        wizard_id = data["wizard_id"]
        company = self.env["res.company"].browse(data["company_id"])
        company_id = data["company_id"]
        partner_ids = data["partner_ids"]
        journal_ids = data["journal_ids"]
        account_ids = data["account_ids"]
        date_to = data["date_to"]
        date_from = data["date_from"]
        hide_account_at_0 = data["hide_account_at_0"]
        show_hierarchy = data["show_hierarchy"]
        show_hierarchy_level = data["show_hierarchy_level"]
        foreign_currency = data["foreign_currency"]
        only_posted_moves = data["only_posted_moves"]
        unaffected_earnings_account = data["unaffected_earnings_account"]
        fy_start_date = data["fy_start_date"]
        wizard = self.env["trial.balance.report.wizard"].browse(wizard_id)
        grouped_by = wizard.grouped_by
        tb_data, accounts_data = self._get_data(
            account_ids,
            journal_ids,
            partner_ids,
            company_id,
            date_to,
            date_from,
            foreign_currency,
            only_posted_moves,
            show_partner_details,
            hide_account_at_0,
            unaffected_earnings_account,
            fy_start_date,
            grouped_by,
        )
        # total_amount, accounts_data, partners_data = self._get_data(
        #     account_ids,
        #     journal_ids,
        #     partner_ids,
        #     company_id,
        #     date_to,
        #     date_from,
        #     foreign_currency,
        #     only_posted_moves,
        #     show_partner_details,
        #     hide_account_at_0,
        #     unaffected_earnings_account,
        #     fy_start_date,
        #     grouped_by
        # )
        # trial_balance = []
        # if not show_partner_details:
        #     for account_id in accounts_data.keys():
        #         accounts_data[account_id].update(
        #             {
        #                 "initial_balance": total_amount[account_id]["initial_balance"],
        #                 "credit": total_amount[account_id]["credit"],
        #                 "debit": total_amount[account_id]["debit"],
        #                 "balance": total_amount[account_id]["balance"],
        #                 "ending_balance": total_amount[account_id]["ending_balance"],
        #                 "type": "account_type",
        #             }
        #         )
        #         if foreign_currency:
        #             accounts_data[account_id].update(
        #                 {
        #                     "ending_currency_balance": total_amount[account_id][
        #                         "ending_currency_balance"
        #                     ],
        #                     "initial_currency_balance": total_amount[account_id][
        #                         "initial_currency_balance"
        #                     ],
        #                 }
        #             )
        #     if show_hierarchy:
        #         groups_data = self._get_groups_data(
        #             accounts_data, total_amount, foreign_currency
        #         )
        #         trial_balance = list(groups_data.values())
        #         trial_balance += list(accounts_data.values())
        #         trial_balance = sorted(trial_balance, key=lambda k: k["complete_code"])
        #         for trial in trial_balance:
        #             counter = trial["complete_code"].count("/")
        #             trial["level"] = counter
        #     else:
        #         trial_balance = list(accounts_data.values())
        #         trial_balance = sorted(trial_balance, key=lambda k: k["code"])
        # else:
        #     if foreign_currency:
        #         for account_id in accounts_data.keys():
        #             total_amount[account_id]["currency_id"] = accounts_data[account_id][
        #                 "currency_id"
        #             ]
        #             total_amount[account_id]["currency_name"] = accounts_data[
        #                 account_id
        #             ]["currency_name"]
        trial_balance = self._create_trial_balance(
            tb_data,
            show_partner_details,
            show_hierarchy,
            foreign_currency,
            accounts_data,
            grouped_by,
            hide_account_at_0,
        )
        # if show_partner_details and foreign_currency:
        #     for a_id in accounts_data.keys():
        #         total_amount[a_id]["currency_id"] = accounts_data[a_id]["currency_id"]
        #         total_amount[a_id]["currency_name"] = accounts_data[a_id]["currency_name"]
        print({"trial_balance": trial_balance})
        print(asas)
        return {
            "doc_ids": wizard.ids,
            "doc_model": wizard._name,
            "docs": wizard,
            "foreign_currency": data["foreign_currency"],
            "company_name": company.display_name,
            "company_currency": company.currency_id,
            "currency_name": company.currency_id.name,
            "date_from": data["date_from"],
            "date_to": data["date_to"],
            "only_posted_moves": data["only_posted_moves"],
            "hide_account_at_0": data["hide_account_at_0"],
            "show_partner_details": data["show_partner_details"],
            "limit_hierarchy_level": data["limit_hierarchy_level"],
            "show_hierarchy": show_hierarchy,
            "hide_parent_hierarchy_level": data["hide_parent_hierarchy_level"],
            "trial_balance": trial_balance,
            # "total_amount": total_amount,
            "accounts_data": accounts_data,
            # "partners_data": partners_data,
            "show_hierarchy_level": show_hierarchy_level,
        }

    def _create_account(self, account, acc_id, data):
        move_lines = []
        for ml_id in data[acc_id].keys():
            if not isinstance(ml_id, int):
                account.update({ml_id: data[acc_id][ml_id]})
            else:
                move_lines += [data[acc_id][ml_id]]
        move_lines = sorted(move_lines, key=lambda k: (k["date"]))
        move_lines = self._recalculate_cumul_balance(
            move_lines,
            data[acc_id]["init_bal"]["balance"],
        )
        account.update({"move_lines": move_lines})
        return account

    def _create_account_not_show_item(self, account, acc_id, data, grouped_by):
        move_lines = []
        for prt_id in data[acc_id].keys():
            if not isinstance(prt_id, int):
                account.update({prt_id: data[acc_id][prt_id]})
            elif isinstance(data[acc_id][prt_id], dict):
                for ml_id in data[acc_id][prt_id].keys():
                    if isinstance(ml_id, int):
                        move_lines += [data[acc_id][prt_id][ml_id]]
        move_lines = sorted(move_lines, key=lambda k: (k["date"]))
        move_lines = self._recalculate_cumul_balance(
            move_lines,
            data[acc_id]["init_bal"]["balance"],
        )
        account.update({"move_lines": move_lines, grouped_by: False})
        return account

    @api.model
    def _recalculate_cumul_balance(self, move_lines, last_cumul_balance):
        for move_line in move_lines:
            move_line["balance"] += last_cumul_balance
            last_cumul_balance = move_line["balance"]
        return move_lines

    def _get_list_grouped_item(self, data, account, hide_account_at_0, rounding):
        list_grouped = []
        for data_id in data.keys():
            group_item = {}
            move_lines = []
            if not isinstance(data_id, int):
                account.update({data_id: data[data_id]})
            else:
                for ml_id in data[data_id].keys():
                    if not isinstance(ml_id, int):
                        group_item.update({ml_id: data[data_id][ml_id]})
                    else:
                        move_lines += [data[data_id][ml_id]]
                move_lines = sorted(move_lines, key=lambda k: (k["date"]))
                move_lines = self._recalculate_cumul_balance(
                    move_lines,
                    data[data_id]["init_bal"]["balance"],
                )
                group_item.update({"move_lines": move_lines})
                if (
                    hide_account_at_0
                    and float_is_zero(
                        data[data_id]["init_bal"]["balance"],
                        precision_rounding=rounding,
                    )
                    and group_item["move_lines"] == []
                ):
                    continue
                list_grouped += [group_item]
        return account, list_grouped

    @api.model
    def _get_move_line_data(self, move_line):
        return {
            "id": move_line["id"],
            "date": move_line["date"],
            "entry": move_line["move_name"],
            "entry_id": move_line["move_id"][0],
            "account_id": move_line["account_id"][0],
            "debit": move_line["debit"],
            "credit": move_line["credit"],
            "balance": move_line["balance"],
            "bal_curr": move_line["amount_currency"],
        }

    def _prepare_ml_items(self, move_line, grouped_by):
        res = []
        if grouped_by == "analytic_account":
            item_id = (
                move_line["analytic_account_id"][0]
                if move_line["analytic_account_id"]
                else 0
            )
            item_name = (
                move_line["analytic_account_id"][1]
                if move_line["analytic_account_id"]
                else _("Missing Analytic Account")
            )
            res.append({"id": item_id, "name": item_name})
        else:
            res.append({"id": 0, "name": ""})
        return res

    def _initialize_data(self, foreign_currency):
        res = {}
        for key_bal in ["init_bal", "fin_bal"]:
            res[key_bal] = {}
            for key_field in ["balance", "credit", "debit"]:
                res[key_bal][key_field] = 0.0
            if foreign_currency:
                res[key_bal]["bal_curr"] = 0.0
        return res

    def _get_ml_fields(self):
        return self.COMMON_ML_FIELDS + [
            "analytic_account_id",
            "credit",
            "debit",
            "amount_currency",
            "balance",
            "move_name",
        ]
