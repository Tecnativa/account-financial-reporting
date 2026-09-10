import {Component, onWillStart, useState} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {AccountReportContent} from "./AccountReportContent/accountReportContent.esm";
import {AccountReportHeader} from "./AccountReportHeader/accountReportHeader.esm";
import {AccountReportSidebar} from "./AccountReportSidebar/accountReportSidebar.esm";
import {getReportAdapter} from "./Adapters/reportAdapterLoader.esm";
import {Layout} from "@web/search/layout";

export class AccountReportView extends Component {
    static template = "account_financial_report.AccountReportView";

    static components = {
        AccountReportSidebar,
        AccountReportHeader,
        AccountReportContent,
        Layout,
    };

    setup() {
        this.orm = useService("orm");
        this.ui = useService("ui");
        this.env = useState({
            pagination: {
                offset: 0,
                limit: 10,
            },
        });
        this.params = this.props.action.params;
        onWillStart(async () => await this.loadReport());
    }

    async loadReport() {
        this.ui.block();
        try {
            const datas = await this.orm.call(
                this.params.report_model,
                "get_report_values",
                [[this.params.active_id], this.params.data]
            );
            console.log(datas);
            const [vals] = await Promise.all([this._prepareVals(datas)]);
            Object.assign(this.env, vals);
        } finally {
            this.ui.unblock();
        }
    }

    async _prepareVals(datas) {
        const Adapter = getReportAdapter(this.params.report_type, datas, this.params);
        return await Adapter.adapt();
    }
}

registry.category("actions").add("account_report_view", AccountReportView);
