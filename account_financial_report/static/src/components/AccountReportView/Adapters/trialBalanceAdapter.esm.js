import {ReportAdapter} from "./reportAdapter.esm";
import {reportAdapterRegistry} from "./registry.esm";
import {_t} from "@web/core/l10n/translation";
import {formatDate, formatMonetary} from "@web/views/fields/formatters";

export class TrialBalanceAdapter extends ReportAdapter {
    getHeader() {
        return {
            company_name: this.datas.company_name,
            company_currency: this.datas.company_currency,
            currency_name: this.datas.currency_name,
            report_name: this.params.report_name,
        };
    }

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

    extraData() {
        const res = super.extraData();
        Object.assign(res, {
            options: this._getOptions(),
        });
        return res;
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
            ...this._getCommonColumns(),
        ];
    }

    _getShowPartnerDetailsColumns() {
        return [
            {
                key: "partner",
                label: _t("Partner"),
                show: true,
            },
            ...this._getCommonColumns(),
        ];
    }

    _getTrialBalances() {
        const array = [];
        const currencyId = this._getCurrency();
        const ids = this.datas.trial_balance.map((account) => account.id);
        for (const id of ids) {
            var trialBalance = this.datas.trial_balance.find(
                (account) => account.id === id
            );
            array.push({
                id: id,
                values: [
                    {
                        key: "code",
                        value: trialBalance.code,
                    },
                    {
                        key: "account",
                        value: trialBalance.name,
                    },
                    ...this._getCommonRows(
                        trialBalance,
                        trialBalance.currency_id ? trialBalance.currency_id : currencyId
                    ),
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
                        ...this._getCommonRows(
                            partnerData,
                            partnerData.currency_id
                                ? partnerData.currency_id
                                : currencyId
                        ),
                    ],
                });
            }
            console.log(amount[1]);
            array.push({
                id: amount[0],
                account: {
                    code: account.code,
                    name: account.name,
                },
                partners: partners,
                values: this._getTotalValues(amount[1], currencyId),
            });
        }
        return array;
    }

    _getOptions() {
        return {
            showPartnerDetails: this.datas.show_partner_details,
            reportType: this.params.report_type,
        };
    }

    _getCommonColumns() {
        return [
            {
                key: "initial_balance",
                label: _t("Initial balance"),
                show: true,
                clickable: true,
            },
            {
                key: "debit",
                label: _t("Debit"),
                show: true,
                clickable: true,
            },
            {
                key: "credit",
                label: _t("Credit"),
                show: true,
                clickable: true,
            },
            {
                key: "period_balance",
                label: _t("Period Balance"),
                show: true,
                clickable: true,
            },
            {
                key: "ending_balance",
                label: _t("Ending Balance"),
                show: true,
                clickable: true,
            },
            {
                key: "initial_currency_balance",
                label: _t("Initial Curr Balance"),
                show: this.datas.foreign_currency,
                clickable: true,
            },
            {
                key: "ending_currency_balance",
                label: _t("Ending Curr Balance"),
                show: this.datas.foreign_currency,
                clickable: true,
            },
        ];
    }

    _getCommonRows(data, currencyId) {
        return [
            {
                key: "initial_balance",
                value: formatMonetary(data.initial_balance, {
                    currencyId: currencyId,
                }),
            },
            {
                key: "debit",
                value: formatMonetary(data.debit, {
                    currencyId: currencyId,
                }),
            },
            {
                key: "credit",
                value: formatMonetary(data.credit, {
                    currencyId: currencyId,
                }),
            },
            {
                key: "period_balance",
                value: formatMonetary(data.balance, {
                    currencyId: currencyId,
                }),
            },
            {
                key: "ending_balance",
                value: formatMonetary(data.ending_balance, {
                    currencyId: currencyId,
                }),
            },
            {
                key: "initial_currency_balance",
                value: formatMonetary(data.initial_currency_balance, {
                    currencyId: currencyId,
                }),
            },
            {
                key: "ending_currency_balance",
                value: formatMonetary(data.ending_currency_balance, {
                    currencyId: currencyId,
                }),
            },
        ];
    }

    _getTotalValues(data, currencyId) {
        return [
            {
                key: "initial_balance",
                value: formatMonetary(data.initial_balance, {
                    currencyId: currencyId,
                }),
            },
            {
                key: "debit",
                value: formatMonetary(data.debit, {
                    currencyId: currencyId,
                }),
            },
            {
                key: "credit",
                value: formatMonetary(data.credit, {
                    currencyId: currencyId,
                }),
            },
            {
                key: "period_balance",
                value: formatMonetary(data.balance, {
                    currencyId: currencyId,
                }),
            },
            {
                key: "ending_balance",
                value: formatMonetary(data.ending_balance, {
                    currencyId: currencyId,
                }),
            },
            {
                key: "initial_currency_balance",
                value: formatMonetary(data.initial_currency_balance, {
                    currencyId: currencyId,
                }),
            },
            {
                key: "ending_currency_balance",
                value: formatMonetary(data.ending_currency_balance, {
                    currencyId: currencyId,
                }),
            },
        ];
    }
}

reportAdapterRegistry.add("trial_balance", TrialBalanceAdapter);
