"""Invoice Processing helpers mixin — единая точка входа блока (заготовка).

Наследует все 16 core-миксинов домена. Порядок наследования — по алфавиту
сущностей. Конфликтов имён методов нет: имена уникальны по locked names
(ApiMethod). Helpers-методы появятся позже.
"""

from iikocloud.mixins.invoice_processing.disassemble import (
    DisassembleCoreMixin,
)
from iikocloud.mixins.invoice_processing.incoming_invoices import (
    IncomingInvoicesCoreMixin,
)
from iikocloud.mixins.invoice_processing.incoming_returned import (
    IncomingReturnedCoreMixin,
)
from iikocloud.mixins.invoice_processing.incoming_service import (
    IncomingServiceCoreMixin,
)
from iikocloud.mixins.invoice_processing.internal_transfer import (
    InternalTransferCoreMixin,
)
from iikocloud.mixins.invoice_processing.outgoing_invoices import (
    OutgoingInvoicesCoreMixin,
)
from iikocloud.mixins.invoice_processing.outgoing_service import (
    OutgoingServiceCoreMixin,
)
from iikocloud.mixins.invoice_processing.production import (
    ProductionCoreMixin,
)
from iikocloud.mixins.invoice_processing.references import (
    AccountTransactionsCoreMixin,
    CounteragentsCoreMixin,
    DocumentTransactionsCoreMixin,
    InvoiceNomenclatureCoreMixin,
)
from iikocloud.mixins.invoice_processing.returned import (
    ReturnedCoreMixin,
)
from iikocloud.mixins.invoice_processing.sales import (
    SalesCoreMixin,
)
from iikocloud.mixins.invoice_processing.transformation import (
    TransformationCoreMixin,
)
from iikocloud.mixins.invoice_processing.writeoff import (
    WriteoffCoreMixin,
)


class InvoiceProcessingHelpersMixin(
    # Порядок — по алфавиту сущностей (16 core-миксинов).
    AccountTransactionsCoreMixin,
    CounteragentsCoreMixin,
    DisassembleCoreMixin,
    DocumentTransactionsCoreMixin,
    IncomingInvoicesCoreMixin,
    IncomingReturnedCoreMixin,
    IncomingServiceCoreMixin,
    InternalTransferCoreMixin,
    InvoiceNomenclatureCoreMixin,
    OutgoingInvoicesCoreMixin,
    OutgoingServiceCoreMixin,
    ProductionCoreMixin,
    ReturnedCoreMixin,
    SalesCoreMixin,
    TransformationCoreMixin,
    WriteoffCoreMixin,
):
    """Публичный invoice processing mixin (helpers появятся позже)."""
