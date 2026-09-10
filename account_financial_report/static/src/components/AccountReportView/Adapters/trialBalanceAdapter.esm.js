import {ReportAdapter} from "./reportAdapter.esm";
import {reportAdapterRegistry} from "./registry.esm";
import {_t} from "@web/core/l10n/translation";
import {formatDate, formatMonetary} from "@web/views/fields/formatters";

export class TrialBalanceAdapter extends ReportAdapter {
    getFilters() {
        return [
            {
                key: "date_range",
                label: _t("Date Range"),
                value: _t(
                    "From: %s To: %s",
                    formatDate(this.datas.date_from),
                    formatDate(this.datas.date_to)
                ),
            },
            {
                key: "hide_account_at_0",
                label: _t("Account at 0"),
                value: this.datas.hide_account_at_0 ? _t("Hide") : _t("Show"),
            },
            {
                key: "only_posted_moves",
                label: _t("Only Posted Moves"),
                value: this.datas.only_posted_moves
                    ? _t("Posted entries")
                    : _t("All entries"),
            },
            {
                key: "limit_hierarchy_level",
                label: _t("Limit hierarchy levels"),
                value: this.datas.limit_hierarchy_level
                    ? _t("Level %s", this.datas.show_hierarchy_level)
                    : _t("No limit"),
            },
        ];
    }
    getColumns() {
        const showPartnerDetails = this.datas.show_partner_details;
        if (!showPartnerDetails) return this._getTrialBalancesColumns();
        return this._getShowPartnerDetailsColumns();
    }

    getRows() {
        const showPartnerDetails = this.datas.show_partner_details;
        if (!showPartnerDetails) return this._getTrialBalances();
        return this._getShowPartnerDetails();
    }

    _getCurrency() {
        const match = this.datas.company_currency.match(/\((\d+),\)/);
        const currencyId = match ? Number(match[1]) : null;
        return currencyId;
    }

    _getTrialBalancesColumns() {
        return [
            {
                key: "code",
                label: _t("Code"),
                show: true,
            },
            {
                key: "account",
                label: _t("Account"),
                show: true,
            },
            {
                key: "initial_balance",
                label: _t("Initial balance"),
                show: true,
            },
            {
                key: "debit",
                label: _t("Debit"),
                show: true,
            },
            {
                key: "credit",
                label: _t("Credit"),
                show: true,
            },
            {
                key: "period_balance",
                label: _t("Period Balance"),
                show: true,
            },
            {
                key: "ending_balance",
                label: _t("Ending Balance"),
                show: true,
            },
        ];
    }

    _getShowPartnerDetailsColumns() {
        return [
            {
                key: "partner",
                label: _t("Partner"),
                show: true,
            },
            {
                key: "initial_balance",
                label: _t("Initial balance"),
                show: true,
            },
            {
                key: "debit",
                label: _t("Debit"),
                show: true,
            },
            {
                key: "credit",
                label: _t("Credit"),
                show: true,
            },
            {
                key: "period_balance",
                label: _t("Period Balance"),
                show: true,
            },
            {
                key: "ending_balance",
                label: _t("Ending Balance"),
                show: true,
            },
        ];
    }

    _getTrialBalances() {
        const array = [];
        const currencyId = this._getCurrency();
        const ids = this.datas.trial_balance.map((account) => account.id);
        for (const id of ids) {
            var trial_balance = this.datas.trial_balance.find(
                (account) => account.id === id
            );
            array.push({
                id: id,
                showPartnerDetails: false,
                values: [
                    {
                        key: "code",
                        value: trial_balance.code,
                    },
                    {
                        key: "account",
                        value: trial_balance.name,
                    },
                    {
                        key: "initial_balance",
                        value: formatMonetary(trial_balance.initial_balance, {
                            currencyId: currencyId,
                        }),
                    },
                    {
                        key: "debit",
                        value: formatMonetary(trial_balance.debit, {
                            currencyId: currencyId,
                        }),
                    },
                    {
                        key: "credit",
                        value: formatMonetary(trial_balance.credit, {
                            currencyId: currencyId,
                        }),
                    },
                    {
                        key: "period_balance",
                        value: formatMonetary(trial_balance.balance, {
                            currencyId: currencyId,
                        }),
                    },
                    {
                        key: "ending_balance",
                        value: formatMonetary(trial_balance.ending_balance, {
                            currencyId: currencyId,
                        }),
                    },
                ],
            });
        }
        return array;
    }

    _getShowPartnerDetails() {
        const array = [];
        const currencyId = this._getCurrency();
        for (const amount of Object.entries(this.datas.total_amount)) {
            var account = this.datas.accounts_data[amount[0]];
            const partners = [];
            const partnerIds = Object.keys(this.datas.partners_data);
            for (const id of partnerIds) {
                if (!amount[1][id]) continue;
                var partnerData = amount[1][id];
                partners.push({
                    id: amount[0],
                    values: [
                        {
                            key: "partner",
                            value: partnerData.partner_name,
                        },
                        {
                            key: "initial_balance",
                            value: formatMonetary(partnerData.initial_balance, {
                                currencyId: currencyId,
                            }),
                        },
                        {
                            key: "debit",
                            value: formatMonetary(partnerData.debit, {
                                currencyId: currencyId,
                            }),
                        },
                        {
                            key: "credit",
                            value: formatMonetary(partnerData.credit, {
                                currencyId: currencyId,
                            }),
                        },
                        {
                            key: "period_balance",
                            value: formatMonetary(partnerData.balance, {
                                currencyId: currencyId,
                            }),
                        },
                        {
                            key: "ending_balance",
                            value: formatMonetary(partnerData.ending_balance, {
                                currencyId: currencyId,
                            }),
                        },
                    ],
                });
            }
            array.push({
                id: amount[0],
                showPartnerDetails: true,
                account: {
                    code: account.code,
                    name: account.name,
                },
                partners: partners,
            });
        }
        return array;
    }
}

reportAdapterRegistry.add("trial_balance", TrialBalanceAdapter);
