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
            filters: [],
            columns: [],
            rows: [],
            header: {},
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
            const [headerVals, contentVals] = await Promise.all([
                this._prepareHeaderVals(datas),
                this._prepareContentVals(datas),
            ]);
            this.env.header = headerVals;
            this.env.filters = contentVals?.filters || [];
            this.env.columns = contentVals?.columns || [];
            this.env.rows = contentVals?.rows || [];
        } finally {
            this.ui.unblock();
        }
    }

    _prepareHeaderVals(datas) {
        return {
            company_name: datas.company_name,
            company_currency: datas.company_currency,
            currency_name: datas.currency_name,
            report_name: this.params.report_name,
        };
    }

    async _prepareContentVals(datas) {
        const Adapter = getReportAdapter(this.params.report_type, datas);
        return await Adapter.adapt();
    }
}

registry.category("actions").add("account_report_view", AccountReportView);
