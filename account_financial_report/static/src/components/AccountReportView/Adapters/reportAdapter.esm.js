export class ReportAdapter {
    constructor(datas) {
        this.datas = datas;
    }

    async adapt() {
        return {
            columns: this.getColumns(),
            rows: this.getRows(),
            filters: this.getFilters(),
        };
    }

    getColumns() {
        throw new Error("ReportAdapter.getColumns() must be implemented");
    }
    getRows() {
        throw new Error("ReportAdapter.getRows() must be implemented");
    }
    getFilters() {
        throw new Error("ReportAdapter.getFilters() must be implemented");
    }
}
