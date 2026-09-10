import {Component} from "@odoo/owl";
import {AccountReportFilters} from "./AccountReportFilters/accountReportFilters.esm";
import {AccountReportTable} from "./AccountReportTable/accountReportTable.esm";
import {Pager} from "@web/core/pager/pager";

export class AccountReportContent extends Component {
    static template = "account_financial_report.AccountReportContent";

    static components = {
        AccountReportFilters,
        AccountReportTable,
        Pager,
    };

    static props = {
        env: Object,
    };

    setup() {
        super.setup();
        this.env = this.props.env;
        console.log(this.env);
        this.updateFilteredRows();
    }
    get getFilters() {
        return this.env.filters;
    }

    get getRows() {
        return this.env.rows;
    }

    get pagination() {
        return this.env.pagination;
    }

    get getColumns() {
        return this.env.columns;
    }

    get totalRows() {
        return this.getRows.length;
    }

    get filteredRows() {
        return this.env.filteredRows;
    }

    updateFilteredRows() {
        const {offset, limit} = this.pagination;
        this.env.filteredRows = this.getRows.slice(offset, offset + limit);
    }

    onPagerUpdate({offset, limit}) {
        console.log({offset, limit});
        this.env.pagination.offset = offset;
        this.env.pagination.limit = limit;
        this.updateFilteredRows();
    }
}
