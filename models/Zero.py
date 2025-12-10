from odoo import models, api, exceptions

class Zero(models.Model):
    _inherit = 'product.template'

    @api.model
    def check_zero_quantity(self):
        product = self.product_variant_id if self.product_variant_id else self.env['product.product']
        qty_available = product.qty_available if product else 0
        qty_in_cart = 0
        website = self.env['website'].get_current_website()
        order = website.sale_get_order()
        if order:
            for line in order.order_line:
                if line.product_id == product:
                    qty_in_cart += line.product_uom_qty

        effective_qty = qty_available - qty_in_cart

        if effective_qty <= 0:
            return {
                'is_disabled': True,
                'button_class': 'btn btn-secondary js_check_product flex-grow-1',
                'button_text': 'Out of Stock'
            }
        return {
            'is_disabled': False,
            'button_class': 'btn btn-primary js_check_product a-submit flex-grow-1',
            'button_text': 'Add to Cart'
        }


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.constrains('product_uom_qty', 'product_id')
    def _check_stock_availability(self):
        for line in self:
            if line.product_id and line.product_id.type == 'product': 
                qty_available = line.product_id.qty_available
                total_qty_in_order = 0
                for order_line in line.order_id.order_line:
                    if order_line.product_id == line.product_id:
                        total_qty_in_order += order_line.product_uom_qty
                if total_qty_in_order > qty_available:
                    raise exceptions.UserError(
                        f"Cannot add more {line.product_id.name} to the cart. "
                        f"Only {qty_available} units are available in stock."
                    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super(SaleOrderLine, self).create(vals_list)
        for record in records:
            if record.product_id and record.product_id.type == 'product':
                qty_available = record.product_id.qty_available
                total_qty_in_order = 0
                for order_line in record.order_id.order_line:
                    if order_line.product_id == record.product_id:
                        total_qty_in_order += order_line.product_uom_qty
                if total_qty_in_order > qty_available:
                    raise exceptions.UserError(
                        f"Cannot add more {record.product_id.name} to the cart. "
                        f"Only {qty_available} units are available in stock."
                    )
        return records

    def write(self, vals):
        result = super(SaleOrderLine, self).write(vals)
        for record in self:
            if record.product_id and record.product_id.type == 'product':
                qty_available = record.product_id.qty_available
                total_qty_in_order = 0
                for order_line in record.order_id.order_line:
                    if order_line.product_id == record.product_id:
                        total_qty_in_order += order_line.product_uom_qty
                if total_qty_in_order > qty_available:
                    raise exceptions.UserError(
                        f"Cannot update quantity for {record.product_id.name}. "
                        f"Only {qty_available} units are available in stock."
                    )
        return result