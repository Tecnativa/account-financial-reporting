# © 2016 Julien Coux (Camptocamp)
# © 2018 Forest and Biomass Romania SA
# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, models
from odoo.tools.float_utils import float_is_zero


class TrialBalanceReport(models.AbstractModel):
    _name = "report.account_financial_report.trial_balance"
    _description = "Trial Balance Report"
    _inherit = "report.account_financial_report.abstract_report"

    def _initialize_common_data(self):
        return {
            "initial_balance": 0,
            "initial_currency_balance": 0,
            "balance": 0,
            "debit": 0,
            "credit": 0,
            "ending_balance": 0,
            "ending_currency_balance": 0,
        }

    def _initialize_no_group_data(self):
        res = self._initialize_common_data()
        res["id"] = 0
        res["type"] = False
        res["name"] = ""
        res["code"] = ""
        res["data"] = {}
        return res

    def _initialize_account_data(self, account_id):
        res = self._initialize_common_data()
        res["id"] = account_id
        res["type"] = "account_type"
        res["partners"] = {}
        return res

    def _initialize_account_group_data(self, data):
        res = self._initialize_common_data()
        res.update(data)
        res["type"] = "group_type"
        res["account_ids"] = {}
        return res

    def _initialize_partner_data(self, partner_id):
        res = self._initialize_common_data()
        res["id"] = partner_id
        return res

    def _get_ml_fields(self):
        return self.COMMON_ML_FIELDS + [
            "analytic_account_id",
            "account_id",
            "credit",
            "debit",
            "amount_currency",
            "balance",
        ]

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

    def _prepare_tb_initial_data(self, tb_initial_data, show_partner_details):
        """Basic method no grouping, the idea is to have all the information
        structured.
        Example data:
        {
            'id': 10,
            'type': 'analytic_type'
            'name': 'Analytic Account',
            'code': 'Code',
            ....
            'data': {
                100: {
                    'id': 100,
                    'name': 'Account',
                    'code': 100,
                    'type': 'account_type',
                    ...
                    'partners': {
                        1000: {
                            'id': 1000,
                            'name': 'Test partner',
                            ...
                        }
                    }
                }
            }
        }."""
        res = self._initialize_no_group_data()
        data = self._prepare_tb_initial_data_misc(tb_initial_data, show_partner_details)
        initial_balance = 0
        initial_currency_balance = 0
        for a_id in list(data.keys()):
            initial_balance += data[a_id]["initial_balance"]
            initial_currency_balance += data[a_id]["initial_currency_balance"]
        res["data"] = data
        res["initial_balance"] = initial_balance
        res["initial_currency_balance"] = initial_currency_balance
        return {0: res}

    def _prepare_tb_initial_data_misc(self, tb_initial_data, show_partner_details):
        """ "Method for processing the data of accounts, can be called by other methods
        with groupings."""
        data = {}
        for tb in tb_initial_data:
            acc_id = tb["account_id"][0]
            data[acc_id] = self._initialize_account_data(acc_id)
            data[acc_id]["initial_balance"] = tb["balance"]
            data[acc_id]["initial_currency_balance"] = tb["amount_currency"]
            if not show_partner_details:
                continue
            tb_initial_partner = self.env["account.move.line"].read_group(
                domain=tb["__domain"],
                fields=["partner_id", "balance", "amount_currency"],
                groupby=["partner_id"],
            )
            partners_data = {}
            for p in tb_initial_partner:
                p_id = p["partner_id"][0]
                partners_data[p_id] = self._initialize_partner_data(p_id)
                partners_data[p_id]["initial_balance"] = p["balance"]
                partners_data[p_id]["initial_currency_balance"] = p["amount_currency"]
            data[acc_id]["partners"] = partners_data
        return data

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

    def _get_initial_balance_data(
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
        if account_ids:
            # If explicit list of accounts is provided,
            # don't include unaffected earnings account
            unaffected_earnings_account = False
        initial_domain_bs = self._get_initial_balances_bs_ml_domain(
            account_ids,
            journal_ids,
            partner_ids,
            company_id,
            date_from,
            only_posted_moves,
            show_partner_details,
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
        tb_initial_fields = ["account_id", "balance", "amount_currency"]
        tb_initial_groupby = ["account_id"]
        if show_partner_details:
            tb_initial_fields.append("partner_id")
            tb_initial_groupby.append("partner_id")
        tb_initial_data_bs = self.env["account.move.line"].read_group(
            domain=initial_domain_bs,
            fields=tb_initial_fields,
            groupby=tb_initial_groupby,
        )
        tb_initial_data_pl = self.env["account.move.line"].read_group(
            domain=initial_domain_pl,
            fields=tb_initial_fields,
            groupby=tb_initial_groupby,
        )
        tb_initial_data = tb_initial_data_bs + tb_initial_data_pl
        method_name = "_prepare_tb_initial_data"
        data = getattr(self, method_name)(tb_initial_data, show_partner_details)
        # unaffected_earnings_account process extra
        unaffected_id = unaffected_earnings_account
        initial_domain_fy_pl = self._get_initial_balance_fy_pl_ml_domain(
            account_ids,
            journal_ids,
            partner_ids,
            company_id,
            fy_start_date,
            only_posted_moves,
            show_partner_details,
        )
        tb_initial_data_fy_pl = self.env["account.move.line"].read_group(
            domain=initial_domain_fy_pl,
            fields=["account_id", "balance", "amount_currency"],
            groupby=["account_id"],
        )
        data = self._post_process_initial_balance_data(
            data, tb_initial_data_fy_pl, unaffected_id, grouped_by
        )
        return data

    def _post_process_initial_balance_data(
        self, data, tb_initial_data, unaffected_id, grouped_by
    ):
        if not unaffected_id:
            return data
        accounts_ids = []
        for key in list(data.keys()):
            for a_id in data[key]["data"]:
                if a_id not in accounts_ids:
                    accounts_ids.append(a_id)
        if unaffected_id not in accounts_ids:
            unaffected_data = self._initialize_account_data(unaffected_id)
            total_balance = sum(x["balance"] for x in tb_initial_data)
            total_amount_currency = sum(x["amount_currency"] for x in tb_initial_data)
            unaffected_data["ending_balance"] += total_balance
            unaffected_data["initial_balance"] += total_balance
            unaffected_data["ending_currency_balance"] += total_amount_currency
            unaffected_data["initial_currency_balance"] += total_amount_currency
            # Create if not exists
            key_unaffected_id = 0
            if key_unaffected_id not in data:
                method_name = "_initialize_no_group_data"
                data[key_unaffected_id] = getattr(self, method_name)()
            data[key_unaffected_id]["data"][unaffected_id] = unaffected_data
            # Increase initial_balance (from group)
            data[key_unaffected_id]["initial_balance"] += unaffected_data[
                "initial_balance"
            ]
            data[key_unaffected_id]["initial_currency_balance"] += unaffected_data[
                "initial_currency_balance"
            ]
        return data

    def _get_partners_data(self, partner_ids):
        res = {}
        partners = self.env["res.partner"].search_read(
            domain=[("id", "in", partner_ids)], fields=["id", "name"]
        )
        for partner_data in partners:
            res[partner_data["id"]] = partner_data
        return res

    def _get_account_groups_data(self, account_group_ids):
        """We obtain the corresponding account.group data, the maximum level and
        the groups per level for later use."""
        res = {}
        groups = self.env["account.group"].search_read(
            domain=[("id", "in", account_group_ids)],
            fields=[
                "id",
                "name",
                "code_prefix_start",
                "level",
                "parent_path",
                "parent_id",
            ],
        )
        max_level = 0
        groups_by_level = {}
        for group_data in groups:
            res[group_data["id"]] = group_data
            res[group_data["id"]]["code"] = group_data["code_prefix_start"]
            level_item = group_data["level"]
            if level_item > max_level:
                max_level = level_item
            if level_item not in groups_by_level:
                groups_by_level[level_item] = []
            groups_by_level[level_item].append(group_data["id"])
        return res, max_level, groups_by_level

    def _get_account_groups_hierarchy(self, account_group_ids):
        """According to the indicated account.group records, get the whole hierarchy
        (all parents)."""
        group_ids = []
        for group in self.env["account.group"].search(
            [("id", "in", account_group_ids)]
        ):
            if group.id not in group_ids:
                group_ids.append(group.id)
            parent_id = group.parent_id
            while parent_id:
                if parent_id.id not in group_ids:
                    group_ids.append(parent_id.id)
                parent_id = parent_id.parent_id
        return group_ids

    def _get_account_groups_full_data(self, account_group_ids, accounts_data, data):
        """Iterate all the groups sorted by level (from highest to lowest) to define
        the values (init_bal, fin_bal, end_bal).
        The values will be the sum of the data values of the accounts in the group or
        in the parent group (higher level)."""
        res, max_level, groups_by_level = self._get_account_groups_data(
            self._get_account_groups_hierarchy(account_group_ids)
        )
        if not res:
            return res
        accounts_by_group_id = {}
        for a_key in list(accounts_data.keys()):
            group_id = accounts_data[a_key]["group_id"]
            if group_id not in accounts_by_group_id:
                accounts_by_group_id[group_id] = []
            accounts_by_group_id[group_id].append(a_key)
        # Set values with level
        gv_keys = list(self._initialize_common_data().keys())
        for level in range(max_level, -1, -1):
            for group_id in groups_by_level[level]:
                account_ids = (
                    accounts_by_group_id[group_id]
                    if group_id in accounts_by_group_id
                    else []
                )
                # Set values
                res[group_id]["account_ids"] = account_ids
                for gv_key in gv_keys:
                    res[group_id][gv_key] = 0
                for a_id in account_ids:
                    for gv_key in gv_keys:
                        res[group_id][gv_key] += data[a_id][gv_key]
                if not account_ids:
                    for ag_id in groups_by_level[level + 1]:
                        g_data = res[ag_id]
                        if g_data["parent_id"][0] == group_id:
                            for gv_key in gv_keys:
                                res[group_id][gv_key] += g_data[gv_key]

        # Sorted
        res_data = list(res.values())
        return sorted(res_data, key=lambda k: k["level"])

    def _prepare_period_ml_data(self, tb_data, total_amounts, show_partner_details):
        tb_data[0]["data"] = self._prepare_period_ml_misc(
            tb_data[0]["data"], total_amounts, show_partner_details
        )
        return tb_data

    def _prepare_period_ml_misc(self, tb_data, total_amounts, show_partner_details):
        res = tb_data
        for ml_data in total_amounts:
            acc_id = ml_data["account_id"][0]
            if acc_id not in res.keys():
                res[acc_id] = self._initialize_account_data(acc_id)
            res[acc_id]["balance"] = ml_data["balance"]
            res[acc_id]["debit"] = ml_data["debit"]
            res[acc_id]["credit"] = ml_data["credit"]
            # Partner process
            if not show_partner_details:
                continue
            if "partners" not in res[acc_id]:
                res[acc_id]["partners"] = {}
            total_amounts_partners = self.env["account.move.line"].read_group(
                domain=ml_data["__domain"],
                fields=self._get_ml_fields(),
                groupby="partner_id",
            )
            for p_data in total_amounts_partners:
                p_id = p_data["partner_id"][0]
                if p_id not in res[acc_id]["partners"]:
                    res[acc_id]["partners"][p_id] = self._initialize_partner_data(p_id)
                res[acc_id]["partners"][p_id]["balance"] = p_data["balance"]
                res[acc_id]["partners"][p_id]["debit"] = p_data["debit"]
                res[acc_id]["partners"][p_id]["credit"] = p_data["credit"]
        return res

    def _get_period_ml_data(
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
        tb_data,
        grouped_by,
    ):
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
        groupby_f = ["account_id"]
        if show_partner_details:
            groupby_f.append("partner_id")
        total_amounts = self.env["account.move.line"].read_group(
            domain=period_domain, fields=ml_fields, groupby=groupby_f
        )
        method_name = "_prepare_period_ml_data"
        tb_data = getattr(self, method_name)(
            tb_data, total_amounts, show_partner_details
        )
        # Get all partners_data + accounts_data + analytic_account_data
        accounts_data = self._get_accounts_from_tb_data(tb_data)
        partners_data = self._get_partners_from_tb_data(tb_data, show_partner_details)
        return (tb_data, accounts_data, partners_data)

    def _get_accounts_from_tb_data(self, tb_data):
        account_ids = []
        for key in list(tb_data.keys()):
            tb_data_item = tb_data[key]
            for a_id in list(tb_data_item["data"].keys()):
                if a_id not in account_ids:
                    account_ids.append(a_id)
        return self._get_accounts_data(account_ids)

    def _get_partners_from_tb_data(self, tb_data, show_partner_details):
        if not show_partner_details:
            return False
        partner_ids = []
        for key in list(tb_data.keys()):
            for a_id in list(tb_data[key]["data"].keys()):
                for p_id in list(tb_data[key]["data"][a_id]["partners"].keys()):
                    if p_id not in partner_ids:
                        partner_ids.append(p_id)
        return self._get_partners_data(partner_ids)

    def is_removable(self, item, rounding):
        return (
            float_is_zero(item["initial_balance"], precision_rounding=rounding)
            and float_is_zero(item["credit"], precision_rounding=rounding)
            and float_is_zero(item["debit"], precision_rounding=rounding)
            and float_is_zero(item["ending_balance"], precision_rounding=rounding)
        )

    def _remove_accounts_0(self, tb_data, company_id):
        """Remove the accounts at 0 (if applicable) from each data key."""
        company = self.env["res.company"].browse(company_id)
        rounding = company.currency_id.rounding
        accounts_to_remove = {}
        for key in list(tb_data.keys()):
            for a_id in list(tb_data[key]["data"].keys()):
                tb_data_item = tb_data[key]["data"][a_id]
            if self.is_removable(tb_data_item, rounding):
                if key not in accounts_to_remove:
                    accounts_to_remove[key] = []
                if a_id not in accounts_to_remove[key]:
                    accounts_to_remove[key].append(a_id)
        keys_to_remove = []
        for key in list(accounts_to_remove.keys()):
            for a_id in accounts_to_remove[key]:
                if a_id in list(tb_data[key]["data"].keys()):
                    del tb_data[key]["data"][a_id]
            # Remove if data is empty
            if len(tb_data[key]["data"]) == 0 and key not in keys_to_remove:
                keys_to_remove.append(key)
        for key in keys_to_remove:
            if key in tb_data:
                del tb_data[key]
        return tb_data

    def _create_trial_balance(
        self,
        tb_data,
        accounts_data,
        partners_data,
        company_id,
        hide_account_at_0,
        show_partner_details,
        show_hierarchy,
        show_hierarchy_level,
        unaffected_id,
        grouped_by,
    ):
        """Generate the data for the report:
        - Remove the accounts at 0 (if applicable).
        - Fill in the groups information and add them as report records
        (key=group_type).
        At the end, we sort the records by code so that they will be displayed
        correctly."""
        if hide_account_at_0:
            tb_data = self._remove_accounts_0(tb_data, company_id)
        # Fill account information + hierarchy data + ending balance
        for key in list(tb_data.keys()):
            for a_id in list(tb_data[key]["data"].keys()):
                tb_item = tb_data[key]["data"][a_id]
                a_data_item = accounts_data[a_id]
                tb_data[key]["data"][a_id]["name"] = a_data_item["name"]
                tb_data[key]["data"][a_id]["code"] = a_data_item["code"]
                tb_data[key]["data"][a_id]["currency_id"] = a_data_item["currency_id"]
                if show_hierarchy:
                    tb_data[key]["data"][a_id]["group_id"] = a_data_item["group_id"]
                # Set ending_balance fields (from account)
                tb_data[key]["data"][a_id]["ending_balance"] = (
                    tb_item["initial_balance"] + tb_item["balance"]
                )
                tb_data[key]["data"][a_id]["ending_currency_balance"] = (
                    tb_item["initial_currency_balance"] + tb_item["balance"]
                )
                # Fill partner information + ending balance
                if not show_partner_details:
                    continue
                for p_id in list(tb_data[key]["data"][a_id]["partners"].keys()):
                    tb_data[key]["data"][a_id]["partners"][p_id][
                        "name"
                    ] = partners_data[p_id]["name"]
                    # Ending balance partner
                    p_item = tb_data[key]["data"][a_id]["partners"][p_id]
                    tb_data[key]["data"][a_id]["partners"][p_id]["ending_balance"] = (
                        p_item["initial_balance"] + p_item["balance"]
                    )
                    tb_data[key]["data"][a_id]["partners"][p_id][
                        "ending_currency_balance"
                    ] = (p_item["initial_currency_balance"] + p_item["balance"])
                tb_data[key]["data"][a_id]["partner_ids"] = list(
                    tb_data[key]["data"][a_id]["partners"].keys()
                )
                # Sort partners
                partnes_account = list(tb_data[key]["data"][a_id]["partners"].values())
                tb_data[key]["data"][a_id]["partners"] = sorted(
                    partnes_account, key=lambda k: k["name"]
                )
            # Set ending_balance fields (from group)
            tb_data[key]["ending_balance"] = (
                tb_data[key]["initial_balance"] + tb_data[key]["balance"]
            )
            tb_data[key]["ending_currency_balance"] = (
                tb_data[key]["initial_currency_balance"] + tb_data[key]["balance"]
            )
        # Show hierarchy process
        if show_hierarchy:
            # Do the process for each item, each grouping will have its own data and
            # its own different account groups according to the accounts it contains.
            for tb_key in list(tb_data.keys()):
                tb_data_item = tb_data[tb_key]
                # Obtain account_groups_data from the item in which we are tb_data_item
                account_group_ids = []
                for a_id in list(tb_data_item["data"].keys()):
                    account_item = tb_data_item["data"][a_id]
                    if (
                        account_item["group_id"]
                        and account_item["group_id"] not in account_group_ids
                    ):
                        account_group_ids.append(account_item["group_id"])
                account_groups_data = self._get_account_groups_full_data(
                    account_group_ids, accounts_data, tb_data_item["data"]
                )
                # Override tb_data: Groups + accounts
                new_tb_data_item = {}
                for ag_data_item in account_groups_data:
                    key = "GROUP-%s" % ag_data_item["id"]
                    new_tb_data_item[key] = ag_data_item
                    new_tb_data_item[key]["type"] = "group_type"
                    for a_id in ag_data_item["account_ids"]:
                        key = "ACCOUNT-%s" % a_id
                        new_tb_data_item[key] = tb_data_item["data"][a_id]
                        new_tb_data_item[key]["level"] = ag_data_item["level"]
                tb_data[tb_key]["data"] = new_tb_data_item
        # Sort trial balance
        tb_data = list(tb_data.values())
        tb_data = sorted(tb_data, key=lambda k: k["code"])
        return tb_data

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
        grouped_by = False
        tb_data = self._get_initial_balance_data(
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
        tb_data, accounts_data, partners_data = self._get_period_ml_data(
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
            tb_data,
            grouped_by,
        )
        trial_balance = self._create_trial_balance(
            tb_data,
            accounts_data,
            partners_data,
            company_id,
            hide_account_at_0,
            show_partner_details,
            show_hierarchy,
            show_hierarchy_level,
            unaffected_earnings_account,
            grouped_by,
        )
        return {
            "doc_ids": [wizard_id],
            "doc_model": "trial.balance.report.wizard",
            "docs": self.env["trial.balance.report.wizard"].browse(wizard_id),
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
            "accounts_data": accounts_data,
            "partners_data": partners_data,
            "show_hierarchy_level": show_hierarchy_level,
        }
