import {Component} from "@odoo/owl";
import {AccountReportLines} from "../AccountReportLines/accountReportLines.esm";

export class AccountReportTrialBalance extends Component {
    static template = "account_financial_report.AccountReportTrialBalance";

    static props = {
        env: Object,
    };

    static components = {
        AccountReportLines,
    };

    setup() {
        super.setup();
        this.env = this.props.env;
    }

    get getRows() {
        return this.env.filteredRows;
    }

    get getColumns() {
        return this.env.columns;
    }

    get options() {
        return this.env.options;
    }
}
