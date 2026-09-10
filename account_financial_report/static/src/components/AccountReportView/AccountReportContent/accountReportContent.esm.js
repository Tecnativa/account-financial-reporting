import {Component} from "@odoo/owl";
import {AccountReportFilters} from "./AccountReportFilters/accountReportFilters.esm";
import {AccountReportTrialBalance} from "./AccountReportTrialBalance/accountReportTrialBalance.esm";
import {Pager} from "@web/core/pager/pager";

export class AccountReportContent extends Component {
    static template = "account_financial_report.AccountReportContent";

    static components = {
        AccountReportFilters,
        AccountReportTrialBalance,
        Pager,
    };

    static props = {
        env: Object,
    };

    components_map = {
        trial_balance: AccountReportTrialBalance,
    };

    setup() {
        super.setup();
        this.env = this.props.env;
        this.env.filteredRows = [];
        this.updateFilteredRows();
        console.log(this.env);
    }

    get pagination() {
        return this.env.pagination;
    }

    get totalRows() {
        return this.env.rows.length;
    }

    updateFilteredRows() {
        const {offset, limit} = this.pagination;
        this.env.filteredRows = this.env.rows.slice(offset, offset + limit);
    }

    onPagerUpdate({offset, limit}) {
        this.env.pagination.offset = offset;
        this.env.pagination.limit = limit;
        this.updateFilteredRows();
    }

    get component() {
        return this.components_map[this.env.options.reportType];
    }
}
