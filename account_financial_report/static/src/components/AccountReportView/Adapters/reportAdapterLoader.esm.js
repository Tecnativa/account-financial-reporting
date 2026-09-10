import {reportAdapterRegistry} from "./registry.esm";

export function getReportAdapter(reportType, datas) {
    const Adapter = reportAdapterRegistry.get(reportType);
    if (!Adapter) {
        throw new Error(`No adapter registered for report type: ${reportType}`);
    }
    return new Adapter(datas);
}
