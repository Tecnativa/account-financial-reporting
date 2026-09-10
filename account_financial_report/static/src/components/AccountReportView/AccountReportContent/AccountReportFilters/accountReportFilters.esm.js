import {Component} from "@odoo/owl";

export class AccountReportFilters extends Component {
    static template = "account_financial_report.AccountReportFilters";

    static props = {
        env: Object,
    };

    setup() {
        super.setup();
        this.env = this.props.env;
    }

    get filters() {
        return this.env.filters;
    }
}
