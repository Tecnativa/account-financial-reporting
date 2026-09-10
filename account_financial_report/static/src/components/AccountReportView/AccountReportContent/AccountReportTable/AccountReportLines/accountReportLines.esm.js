import {Component} from "@odoo/owl";

export class AccountReportLines extends Component {
    static template = "account_financial_report.AccountReportLines";

    static props = {
        row: Object,
        columns: Object,
    };

    setup() {
        super.setup();
    }

    get columns() {
        return this.props.columns;
    }
    get row() {
        return this.props.row;
    }
}
