import {Component} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";

export class AccountReportLines extends Component {
    static template = "account_financial_report.AccountReportLines";

    static props = {
        row: Object,
        columns: Object,
    };

    setup() {
        super.setup();
        this.action = useService("action");
    }

    get columns() {
        return this.props.columns;
    }
    get row() {
        return this.props.row;
    }

    openMoveLines(row, key) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "account.move.line",
            domain: [["account_id", "in", [row.id]]],
            views: [[false, "list"]],
            context: {
                create: false,
                edit: false,
                delete: false,
            },
            search_view_id: false,
            target: "new",
        });
        console.log(row, key);
    }
}
