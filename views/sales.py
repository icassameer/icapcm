# ============================================================
#  ICA PMS — Sales & Invoices  (GST + Print)
# ============================================================

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import os, sys, datetime, tempfile, subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from utils.helpers import (DataTable, make_btn, make_green_btn, make_danger_btn,
                            card_frame, show_toast, format_currency, format_date,
                            today_str, month_start_str)

GST_RATES = ['0', '5', '12', '18', '28']


class SalesView(ctk.CTkFrame):
    def __init__(self, parent, db, user, **kwargs):
        super().__init__(parent, fg_color=config.BG, **kwargs)
        self.db   = db
        self.user = user
        self._cache = []
        self._build()
        self.load_sales()

    # ─────────────────────────────────────────────────────────
    def _build(self):
        # ── Toolbar ──────────────────────────────────────────
        tb = ctk.CTkFrame(self, fg_color='white', height=60)
        tb.pack(fill='x')
        tb.pack_propagate(False)
        ctk.CTkLabel(tb, text='💰  Sales & Invoices',
                      font=('Segoe UI', 18, 'bold'),
                      text_color=config.PRIMARY).pack(side='left', padx=20, pady=14)
        make_green_btn(tb, '+ New Sale', self.new_sale_dialog,
                       width=130, height=36).pack(side='right', padx=16, pady=12)

        # ── Summary cards ────────────────────────────────────
        self.summary = ctk.CTkFrame(self, fg_color='transparent')
        self.summary.pack(fill='x', padx=16, pady=(8, 4))

        # ── Filter bar ───────────────────────────────────────
        fb = ctk.CTkFrame(self, fg_color='white', height=50)
        fb.pack(fill='x')
        fb.pack_propagate(False)
        inn = ctk.CTkFrame(fb, fg_color='transparent')
        inn.pack(side='left', padx=12, pady=7)

        ctk.CTkLabel(inn, text='From:', font=('Segoe UI', 11),
                      text_color=config.TEXT_MID).pack(side='left', padx=(0,4))
        self.from_var = ctk.StringVar(value=month_start_str())
        ctk.CTkEntry(inn, textvariable=self.from_var, width=110, height=32,
                      fg_color='white', border_color='#D1D5DB',
                      text_color=config.TEXT_DARK).pack(side='left')

        ctk.CTkLabel(inn, text='To:', font=('Segoe UI', 11),
                      text_color=config.TEXT_MID).pack(side='left', padx=(10,4))
        self.to_var = ctk.StringVar(value=today_str())
        ctk.CTkEntry(inn, textvariable=self.to_var, width=110, height=32,
                      fg_color='white', border_color='#D1D5DB',
                      text_color=config.TEXT_DARK).pack(side='left')

        make_btn(inn, '🔍 Filter', self.load_sales, width=90, height=32).pack(side='left', padx=8)
        for lbl, d in [('Today',0),('Week',7),('Month',30)]:
            make_btn(inn, lbl, lambda x=d: self._quick(x),
                      color='#F3F4F6', hover='#E5E7EB', width=60, height=32
                      ).pack(side='left', padx=2)

        self.count_lbl = ctk.CTkLabel(fb, text='', font=('Segoe UI', 11),
                                       text_color=config.TEXT_MID)
        self.count_lbl.pack(side='right', padx=16)

        # ── Table (fills all remaining space) ────────────────
        tf = ctk.CTkFrame(self, fg_color='white', corner_radius=12)
        tf.pack(fill='both', expand=True, padx=16, pady=(4, 12))
        tf.grid_rowconfigure(0, weight=1)
        tf.grid_columnconfigure(0, weight=1)

        cols = ('Invoice No','Date','Customer','Items',
                'Subtotal','Discount','GST','Net Amount','Payment','User')
        cw   = {'Invoice No':130,'Date':120,'Customer':130,'Items':50,
                 'Subtotal':90,'Discount':75,'GST':90,
                 'Net Amount':105,'Payment':85,'User':100}
        self.table = DataTable(tf, cols, cw)
        self.table.grid(row=0, column=0, sticky='nsew', padx=8, pady=8)
        self.table.bind_double(lambda e: self._view_invoice())

    # ─────────────────────────────────────────────────────────
    def load_sales(self):
        sales = self.db.get_sales(self.from_var.get(), self.to_var.get())
        rows, rev, gst_total = [], 0, 0
        for s in sales:
            itms  = self.db.get_sale_items(s['id'])
            rev  += s.get('net_amount', 0) or 0
            gst_total += s.get('gst_amount', 0) or 0
            rows.append((
                s.get('invoice_no',''),
                format_date(s.get('created_at','')),
                s.get('customer_name','') or 'Walk-in',
                len(itms),
                format_currency(s.get('total_amount',0)),
                format_currency(s.get('discount',0)),
                f"{s.get('gst_rate',0) or 0}% / {format_currency(s.get('gst_amount',0) or 0)}",
                format_currency(s.get('net_amount',0)),
                s.get('payment_method',''),
                s.get('user_name',''),
            ))
        self.table.load_raw(rows)
        self.count_lbl.configure(
            text=f'{len(sales)} invoices  |  Revenue: {format_currency(rev)}')
        self._cache = sales
        self._update_summary(sales, rev, gst_total)

    def refresh(self):
        self.load_sales()

    def _quick(self, days):
        today = datetime.date.today()
        self.from_var.set(today.isoformat() if days == 0
                          else (today - datetime.timedelta(days=days)).isoformat())
        self.to_var.set(today.isoformat())
        self.load_sales()

    def _update_summary(self, sales, rev, gst_total):
        for w in self.summary.winfo_children():
            w.destroy()
        cash = sum(s.get('net_amount',0) or 0 for s in sales
                    if s.get('payment_method')=='Cash')
        for title, val, sub, col in [
            ('Total Sales',   str(len(sales)),         'Invoices',      config.PRIMARY),
            ('Revenue',       format_currency(rev),    'Net amount',    '#10B981'),
            ('GST Collected', format_currency(gst_total),'Tax total',   '#7C3AED'),
            ('Cash Sales',    format_currency(cash),   'Cash payments', '#0891B2'),
        ]:
            f = ctk.CTkFrame(self.summary, fg_color=col,
                              corner_radius=12, width=195, height=84)
            f.pack(side='left', padx=6)
            f.pack_propagate(False)
            ctk.CTkLabel(f, text=title, font=('Segoe UI', 11),
                          text_color='#BFCFEE').pack(anchor='w', padx=14, pady=(10,0))
            ctk.CTkLabel(f, text=val, font=('Segoe UI', 19, 'bold'),
                          text_color='white').pack(anchor='w', padx=14, pady=2)
            ctk.CTkLabel(f, text=sub, font=('Segoe UI', 9),
                          text_color='#99B0D8').pack(anchor='w', padx=14)

    # ── View Invoice ──────────────────────────────────────────
    def _view_invoice(self):
        v = self.table.selected_values()
        if not v:
            return
        sale  = next((s for s in self._cache if s.get('invoice_no')==v[0]), None)
        if not sale: return
        items = self.db.get_sale_items(sale['id'])

        dlg = ctk.CTkToplevel(self)
        dlg.title(f"Invoice — {v[0]}")
        dlg.geometry('720x560')
        dlg.grab_set()
        dlg.geometry(f"720x560+{self.winfo_rootx()+100}+{self.winfo_rooty()+40}")

        hdr = ctk.CTkFrame(dlg, fg_color=config.PRIMARY, corner_radius=0, height=52)
        hdr.pack(fill='x')
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text=f'🧾  {v[0]}',
                      font=('Segoe UI', 14, 'bold'), text_color='white'
                      ).pack(side='left', padx=20, pady=12)
        make_green_btn(hdr, '🖨 Print / Save PDF',
                       lambda: self._print_invoice(sale, items),
                       width=160, height=34).pack(side='right', padx=16, pady=9)

        # Meta
        mf = ctk.CTkFrame(dlg, fg_color='#F8FAFC')
        mf.pack(fill='x', padx=0)
        row = ctk.CTkFrame(mf, fg_color='transparent')
        row.pack(fill='x', padx=16, pady=10)
        gst_r = sale.get('gst_rate', 0) or 0
        gst_a = sale.get('gst_amount', 0) or 0
        for lbl, val in [
            ('Date',     format_date(sale.get('created_at',''))),
            ('Customer', sale.get('customer_name','') or 'Walk-in'),
            ('Phone',    sale.get('customer_phone','') or '—'),
            ('Payment',  sale.get('payment_method','')),
            (f'GST({gst_r}%)', format_currency(gst_a)),
        ]:
            c = ctk.CTkFrame(row, fg_color='transparent')
            c.pack(side='left', padx=14)
            ctk.CTkLabel(c, text=lbl, font=('Segoe UI', 10),
                          text_color=config.TEXT_MID).pack(anchor='w')
            ctk.CTkLabel(c, text=val, font=('Segoe UI', 12, 'bold'),
                          text_color=config.TEXT_DARK).pack(anchor='w')

        # Items
        ctk.CTkLabel(dlg, text='  Items', font=('Segoe UI', 12, 'bold'),
                      text_color=config.PRIMARY).pack(anchor='w', padx=16, pady=(4,2))
        itf = ctk.CTkFrame(dlg, fg_color='white', corner_radius=10)
        itf.pack(fill='both', expand=True, padx=16, pady=(0,6))
        itf.grid_rowconfigure(0, weight=1)
        itf.grid_columnconfigure(0, weight=1)
        icols = ('SKU','Product','Qty','Unit Price','Total')
        icw   = {'SKU':90,'Product':300,'Qty':60,'Unit Price':110,'Total':110}
        itbl  = DataTable(itf, icols, icw)
        itbl.grid(row=0, column=0, sticky='nsew', padx=6, pady=6)
        itbl.load_raw([(i.get('sku',''), i.get('product_name',''),
                         i.get('quantity',0),
                         format_currency(i.get('unit_price',0)),
                         format_currency(i.get('total_price',0))) for i in items])

        # Totals
        tot = ctk.CTkFrame(dlg, fg_color='#F0F4FF', height=50)
        tot.pack(fill='x', padx=16, pady=(0,12))
        tot.pack_propagate(False)
        sub = sale.get('total_amount',0) or 0
        dis = sale.get('discount',0) or 0
        net = sale.get('net_amount',0) or 0
        ctk.CTkLabel(tot,
                      text=(f"Subtotal: {format_currency(sub)}    "
                             f"Discount: {format_currency(dis)}    "
                             f"GST ({gst_r}%): {format_currency(gst_a)}    "
                             f"NET TOTAL: {format_currency(net)}"),
                      font=('Segoe UI', 12, 'bold'),
                      text_color=config.PRIMARY).pack(side='right', padx=20, pady=12)

    # ── Print Invoice PDF ─────────────────────────────────────
    def _print_invoice(self, sale, items):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.units import mm
            from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                             Paragraph, Spacer, HRFlowable)
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_CENTER, TA_RIGHT
        except ImportError:
            messagebox.showerror('Missing Package',
                'reportlab not installed.\n\nRun: python -m pip install reportlab')
            return

        inv_no = sale.get('invoice_no','INV')
        tmp    = tempfile.NamedTemporaryFile(
            suffix='.pdf', delete=False, prefix=f'{inv_no}_')
        path   = tmp.name
        tmp.close()

        doc    = SimpleDocTemplate(path, pagesize=A4,
                                    leftMargin=14*mm, rightMargin=14*mm,
                                    topMargin=12*mm, bottomMargin=12*mm)
        styles = getSampleStyleSheet()
        C_PRI  = colors.HexColor('#1B2A6B')
        C_ACC  = colors.HexColor('#00D084')
        C_GREY = colors.HexColor('#F8FAFC')
        story  = []

        # ── Company header ────────────────────────────────────
        hdr = Table([[
            Paragraph(f"<font color='white' size='20'><b>{config.APP_NAME}</b></font><br/>"
                       f"<font color='#BFCFEE' size='9'>{config.APP_FULL_NAME}</font>",
                       styles['Normal']),
            Paragraph(f"<font color='#BFCFEE' size='9'>Support: {config.SUPPORT_WHATSAPP}</font>",
                       styles['Normal']),
            Paragraph("<font color='white' size='24'><b>INVOICE</b></font>",
                       ParagraphStyle('r', parent=styles['Normal'], alignment=TA_RIGHT)),
        ]], colWidths=[70*mm, 75*mm, 35*mm])
        hdr.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),(-1,-1), C_PRI),
            ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
            ('TOPPADDING',    (0,0),(-1,-1), 12),
            ('BOTTOMPADDING', (0,0),(-1,-1), 12),
            ('LEFTPADDING',   (0,0),(-1,-1), 8),
        ]))
        story += [hdr, Spacer(1, 5*mm)]

        # ── Bill to / Invoice details ─────────────────────────
        cust    = sale.get('customer_name','') or 'Walk-in'
        phone   = sale.get('customer_phone','') or '—'
        inv_dt  = format_date(sale.get('created_at',''))
        payment = sale.get('payment_method','')
        gst_r   = sale.get('gst_rate',0) or 0
        gst_a   = sale.get('gst_amount',0) or 0

        meta = Table([
            [Paragraph('<b>Bill To</b>', styles['Normal']),
             Paragraph('<b>Invoice Details</b>', styles['Normal'])],
            [Paragraph(f'<b>{cust}</b>', styles['Normal']),
             Paragraph(f'<b>Invoice No:</b> {inv_no}', styles['Normal'])],
            [Paragraph(f'Phone: {phone}', styles['Normal']),
             Paragraph(f'<b>Date:</b> {inv_dt}', styles['Normal'])],
            ['', Paragraph(f'<b>Payment:</b> {payment}', styles['Normal'])],
        ], colWidths=[95*mm, 85*mm])
        meta.setStyle(TableStyle([
            ('BACKGROUND',   (0,0),(-1,0), colors.HexColor('#EEF2FF')),
            ('FONTSIZE',     (0,0),(-1,-1), 9),
            ('TOPPADDING',   (0,0),(-1,-1), 4),
            ('BOTTOMPADDING',(0,0),(-1,-1), 4),
            ('LEFTPADDING',  (0,0),(-1,-1), 8),
            ('GRID',         (0,0),(-1,-1), 0.3, colors.HexColor('#E5E7EB')),
        ]))
        story += [meta, Spacer(1, 4*mm)]

        # ── Items table ───────────────────────────────────────
        # Cell style — enables word wrap
        cs  = ParagraphStyle('cell',  parent=styles['Normal'], fontSize=9,
                              fontName='Helvetica', leading=12)
        csr = ParagraphStyle('cellR', parent=styles['Normal'], fontSize=9,
                              fontName='Helvetica', leading=12, alignment=TA_RIGHT)
        csb = ParagraphStyle('cellH', parent=styles['Normal'], fontSize=9,
                              fontName='Helvetica-Bold', leading=12,
                              textColor=colors.white)
        csbr = ParagraphStyle('cellHR', parent=styles['Normal'], fontSize=9,
                               fontName='Helvetica-Bold', leading=12,
                               textColor=colors.white, alignment=TA_RIGHT)

        rows = [[
            Paragraph('#',          csb),
            Paragraph('SKU',        csb),
            Paragraph('Product',    csb),
            Paragraph('Qty',        csbr),
            Paragraph('Unit Price', csbr),
            Paragraph('Total',      csbr),
        ]]
        for idx, it in enumerate(items, 1):
            rows.append([
                Paragraph(str(idx),                            cs),
                Paragraph(str(it.get('sku','')),               cs),
                Paragraph(str(it.get('product_name','')),      cs),
                Paragraph(str(it.get('quantity',0)),           csr),
                Paragraph(f"Rs. {it.get('unit_price',0):.2f}", csr),
                Paragraph(f"Rs. {it.get('total_price',0):.2f}",csr),
            ])

        # Widths: total must equal page_width - left_margin - right_margin
        # A4=210mm, margins 14+14=28mm → available=182mm
        # #=8, SKU=28, Product=86, Qty=14, UnitPrice=24, Total=22 → 182mm
        it_tbl = Table(rows, colWidths=[8*mm,28*mm,86*mm,14*mm,24*mm,22*mm],
                        repeatRows=1)
        it_tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),(-1,0), C_PRI),
            ('TEXTCOLOR',     (0,0),(-1,0), colors.white),
            ('FONTNAME',      (0,0),(-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0,0),(-1,-1), 9),
            ('ALIGN',         (3,0),(-1,-1), 'RIGHT'),
            ('ALIGN',         (0,0),(0,-1),  'CENTER'),
            ('ROWBACKGROUNDS',(0,1),(-1,-1), [colors.white, C_GREY]),
            ('GRID',          (0,0),(-1,-1), 0.4, colors.HexColor('#E5E7EB')),
            ('TOPPADDING',    (0,0),(-1,-1), 5),
            ('BOTTOMPADDING', (0,0),(-1,-1), 5),
            ('LEFTPADDING',   (0,0),(-1,-1), 5),
        ]))
        story += [it_tbl, Spacer(1, 4*mm)]

        # ── GST Breakdown ─────────────────────────────────────
        sub  = sale.get('total_amount',0) or 0
        disc = sale.get('discount',0) or 0
        net  = sale.get('net_amount',0) or 0

        tot_rows = [
            ['','', 'Subtotal',           f'Rs. {sub:.2f}'],
            ['','', 'Discount (-)',        f'Rs. {disc:.2f}'],
            ['','', f'GST @ {gst_r:.0f}%', f'Rs. {gst_a:.2f}'],
            ['','', 'NET TOTAL',           f'Rs. {net:.2f}'],
        ]
        tot_tbl = Table(tot_rows, colWidths=[90*mm, 18*mm, 50*mm, 26*mm])
        tot_tbl.setStyle(TableStyle([
            ('FONTSIZE',     (0,0),(-1,-1), 9),
            ('ALIGN',        (2,0),(-1,-1), 'RIGHT'),
            ('FONTNAME',     (2,3),(-1,3),  'Helvetica-Bold'),
            ('FONTSIZE',     (2,3),(-1,3),  11),
            ('TEXTCOLOR',    (2,3),(-1,3),  C_PRI),
            ('BACKGROUND',   (2,3),(-1,3),  colors.HexColor('#EEF2FF')),
            ('TOPPADDING',   (0,0),(-1,-1), 3),
            ('BOTTOMPADDING',(0,0),(-1,-1), 3),
            ('LINEABOVE',    (2,3),(-1,3),  1, C_PRI),
        ]))
        story += [tot_tbl, Spacer(1, 5*mm)]
        story.append(HRFlowable(width='100%', thickness=1, color=C_ACC))
        story.append(Spacer(1, 3*mm))

        # GST note
        if gst_r > 0:
            cgst = gst_a / 2
            sgst = gst_a / 2
            story.append(Paragraph(
                f'<font size="8" color="grey">GST Breakup — '
                f'CGST ({gst_r/2:.1f}%): Rs.{cgst:.2f}  |  '
                f'SGST ({gst_r/2:.1f}%): Rs.{sgst:.2f}  |  '
                f'Total GST: Rs.{gst_a:.2f}</font>',
                styles['Normal']))
            story.append(Spacer(1, 3*mm))

        if sale.get('notes'):
            story.append(Paragraph(f'<b>Notes:</b> {sale["notes"]}', styles['Normal']))
            story.append(Spacer(1, 3*mm))

        story.append(Paragraph(
            f'<font size="9" color="grey">Thank you for your business! '
            f'Support: {config.SUPPORT_WHATSAPP}</font>',
            ParagraphStyle('footer', parent=styles['Normal'], alignment=TA_CENTER)))

        doc.build(story)

        # Open PDF
        try:
            os.startfile(path)
        except AttributeError:
            try:    subprocess.Popen(['xdg-open', path])
            except: subprocess.Popen(['open', path])

        show_toast(self, f'✓ Invoice PDF ready — {inv_no}')

    # ── New Sale Dialog ───────────────────────────────────────
    def new_sale_dialog(self):
        dlg = ctk.CTkToplevel(self)
        dlg.title('+ New Sale')
        dlg.geometry('880x730')
        dlg.resizable(True, True)
        dlg.grab_set()
        dlg.geometry(f"880x730+{self.winfo_rootx()+60}+{max(10,self.winfo_rooty()+20)}")

        # Header
        hdr = ctk.CTkFrame(dlg, fg_color=config.PRIMARY, corner_radius=0, height=52)
        hdr.pack(fill='x')
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text='🧾  Create New Sale / Invoice',
                      font=('Segoe UI', 14, 'bold'), text_color='white'
                      ).pack(side='left', padx=20, pady=12)

        # Customer details row
        meta = ctk.CTkFrame(dlg, fg_color='#F8FAFC')
        meta.pack(fill='x')
        m = ctk.CTkFrame(meta, fg_color='transparent')
        m.pack(fill='x', padx=14, pady=10)

        def field(parent, label, w=150, default=''):
            f = ctk.CTkFrame(parent, fg_color='transparent')
            f.pack(side='left', padx=(0, 10))
            ctk.CTkLabel(f, text=label, font=('Segoe UI', 10, 'bold'),
                          text_color=config.TEXT_DARK).pack(anchor='w')
            e = ctk.CTkEntry(f, width=w, height=32, fg_color='white',
                              border_color='#D1D5DB', text_color=config.TEXT_DARK,
                              font=('Segoe UI', 11))
            e.insert(0, default)
            e.pack()
            return e

        def combo_field(parent, label, values, default, w=110):
            f = ctk.CTkFrame(parent, fg_color='transparent')
            f.pack(side='left', padx=(0, 10))
            ctk.CTkLabel(f, text=label, font=('Segoe UI', 10, 'bold'),
                          text_color=config.TEXT_DARK).pack(anchor='w')
            v = ctk.StringVar(value=default)
            ctk.CTkComboBox(f, variable=v, values=values,
                             width=w, height=32, fg_color='white',
                             border_color='#D1D5DB', font=('Segoe UI', 11)).pack()
            return v

        cust_e  = field(m, 'Customer Name', 155)
        phone_e = field(m, 'Phone', 115)
        disc_e  = field(m, 'Discount (₹)', 85, '0')
        gst_var = combo_field(m, 'GST Rate (%)', GST_RATES, '18', 85)
        pay_var = combo_field(m, 'Payment',
                               ['Cash','UPI','Card','Bank Transfer','Credit','Cheque'],
                               'Cash', 130)
        notes_e = field(m, 'Notes', 140)

        # Cart toolbar
        ct = ctk.CTkFrame(dlg, fg_color='white', height=46)
        ct.pack(fill='x')
        ct.pack_propagate(False)
        ctk.CTkLabel(ct, text='  🛒  Cart',
                      font=('Segoe UI', 12, 'bold'), text_color=config.PRIMARY
                      ).pack(side='left', padx=16, pady=12)

        # Cart table — fills available space
        cf = ctk.CTkFrame(dlg, fg_color='white', corner_radius=0)
        cf.pack(fill='both', expand=True, padx=14, pady=(0, 4))
        cf.grid_rowconfigure(0, weight=1)
        cf.grid_columnconfigure(0, weight=1)

        cart_cols = ('SKU','Product','Stock','Qty','Unit Price (₹)','Line Total (₹)')
        cart_cw   = {'SKU':80,'Product':270,'Stock':60,'Qty':55,
                     'Unit Price (₹)':115,'Line Total (₹)':115}
        cart_tbl  = DataTable(cf, cart_cols, cart_cw)
        cart_tbl.grid(row=0, column=0, sticky='nsew', padx=4, pady=4)
        cart_tbl._items = []

        # Add/Remove buttons (AFTER table so they appear below it)
        btn_row = ctk.CTkFrame(dlg, fg_color='#F0F4FF', height=44)
        btn_row.pack(fill='x', padx=14)
        btn_row.pack_propagate(False)
        make_green_btn(btn_row, '+ Add Product',
                       lambda: self._add_item(dlg, cart_tbl, total_lbl, disc_e, gst_var),
                       width=130, height=32).pack(side='left', padx=8, pady=6)
        make_danger_btn(btn_row, '🗑 Remove Selected',
                        lambda: self._remove_item(cart_tbl, total_lbl, disc_e, gst_var),
                        width=150, height=32).pack(side='left', padx=4, pady=6)

        # Totals bar
        tot_bar = ctk.CTkFrame(dlg, fg_color='#1B2A6B', height=48)
        tot_bar.pack(fill='x', padx=14, pady=(2, 4))
        tot_bar.pack_propagate(False)
        total_lbl = ctk.CTkLabel(tot_bar,
                                  text='Subtotal: ₹0.00  |  GST: ₹0.00  |  NET TOTAL: ₹0.00',
                                  font=('Segoe UI', 13, 'bold'), text_color='white')
        total_lbl.pack(side='right', padx=20, pady=12)

        err_lbl = ctk.CTkLabel(dlg, text='', font=('Segoe UI', 11),
                                text_color='#EF4444')
        err_lbl.pack(anchor='w', padx=20)

        # Bottom save bar
        bot = ctk.CTkFrame(dlg, fg_color='white', height=56)
        bot.pack(fill='x', side='bottom')
        bot.pack_propagate(False)

        def recalc(*_):
            try:
                disc  = float(disc_e.get() or 0)
                gst_r = float(gst_var.get() or 0)
            except ValueError:
                return
            sub    = sum(i['total'] for i in cart_tbl._items)
            after  = sub - disc
            gst_a  = round(after * gst_r / 100, 2)
            net    = round(after + gst_a, 2)
            total_lbl.configure(
                text=(f'Subtotal: {format_currency(sub)}  '
                      f'Disc: {format_currency(disc)}  '
                      f'GST({gst_r:.0f}%): {format_currency(gst_a)}  '
                      f'NET TOTAL: {format_currency(net)}'))

        cart_tbl._recalc = recalc
        disc_e.bind('<KeyRelease>', recalc)
        gst_var.trace_add('write', lambda *_: recalc())

        def save_sale():
            if not cart_tbl._items:
                err_lbl.configure(text='⚠ Add at least one product'); return
            try:
                disc  = float(disc_e.get() or 0)
                gst_r = float(gst_var.get() or 0)
            except ValueError:
                err_lbl.configure(text='⚠ Invalid discount or GST value'); return
            try:
                inv_no = self.db.create_sale(
                    customer_name  = cust_e.get().strip() or 'Walk-in',
                    items          = [{'product_id':i['product_id'],
                                       'qty':i['qty'],'unit_price':i['unit_price']}
                                      for i in cart_tbl._items],
                    discount       = disc,
                    payment_method = pay_var.get(),
                    notes          = notes_e.get().strip(),
                    user_id        = self.user['id'],
                    gst_rate       = gst_r,
                    customer_phone = phone_e.get().strip(),
                )
                show_toast(self, f'✓ Invoice {inv_no} saved!')
                self.load_sales()
                if messagebox.askyesno('Print Invoice',
                                        f'Invoice {inv_no} saved!\n\nOpen & print now?'):
                    sale_obj = next((s for s in self._cache
                                     if s.get('invoice_no')==inv_no), None)
                    if sale_obj:
                        self._print_invoice(sale_obj, self.db.get_sale_items(sale_obj['id']))
                dlg.destroy()
            except Exception as ex:
                err_lbl.configure(text=f'Error: {ex}')

        make_green_btn(bot, '💾 Save Invoice', save_sale,
                       width=160, height=40).pack(side='right', padx=16, pady=8)
        make_btn(bot, 'Cancel', dlg.destroy,
                  width=100, height=40).pack(side='right', padx=4, pady=8)

    # ── Add product to cart ───────────────────────────────────
    def _add_item(self, parent, cart_tbl, total_lbl, disc_e, gst_var):
        dlg2 = ctk.CTkToplevel(parent)
        dlg2.title('Select Product')
        dlg2.geometry('700x520')
        dlg2.grab_set()
        dlg2.geometry(f"700x520+{parent.winfo_rootx()+80}+{parent.winfo_rooty()+60}")

        ctk.CTkLabel(dlg2, text='Select Product',
                      font=('Segoe UI', 13, 'bold'), text_color=config.PRIMARY
                      ).pack(padx=20, pady=8)

        sv = ctk.StringVar()
        ctk.CTkEntry(dlg2, textvariable=sv,
                      placeholder_text='Search name or SKU...',
                      width=500, height=34, fg_color='white',
                      border_color='#D1D5DB', text_color=config.TEXT_DARK
                      ).pack(padx=16, pady=(0,6))

        pf = ctk.CTkFrame(dlg2, fg_color='white')
        pf.pack(fill='both', expand=True, padx=12, pady=4)
        pf.grid_rowconfigure(0, weight=1)
        pf.grid_columnconfigure(0, weight=1)
        cols2 = ('SKU','Name','Stock','Unit','Price')
        cw2   = {'SKU':90,'Name':290,'Stock':70,'Unit':60,'Price':100}
        tbl2  = DataTable(pf, cols2, cw2)
        tbl2.grid(row=0, column=0, sticky='nsew', padx=4, pady=4)
        all_p = self.db.get_products()
        tbl2._filtered = all_p

        def load_prods(*_):
            s = sv.get().lower()
            tbl2._filtered = ([p for p in all_p
                                if s in (p['name']+p['sku']).lower()] if s else all_p)
            tbl2.load_raw([(p['sku'],p['name'],p['quantity'],
                             p.get('unit','pcs'),
                             format_currency(p['selling_price']))
                            for p in tbl2._filtered])

        sv.trace_add('write', load_prods)
        load_prods()

        qrow = ctk.CTkFrame(dlg2, fg_color='transparent')
        qrow.pack(pady=6)
        for lbl, w, default, attr in [
            ('Qty:', 70, '1', 'qty_e'),
            ('Price (₹):', 100, '', 'price_e')
        ]:
            ctk.CTkLabel(qrow, text=lbl, font=('Segoe UI', 12, 'bold'),
                          text_color=config.TEXT_DARK).pack(side='left', padx=(6,4))
            e = ctk.CTkEntry(qrow, width=w, height=32, fg_color='white',
                               border_color='#D1D5DB', text_color=config.TEXT_DARK)
            e.insert(0, default)
            e.pack(side='left', padx=(0, 10))
            setattr(dlg2, attr, e)
        err2 = ctk.CTkLabel(qrow, text='', font=('Segoe UI', 11),
                              text_color='#EF4444')
        err2.pack(side='left')

        def on_sel(*_):
            v2 = tbl2.selected_values()
            if v2 and tbl2._filtered:
                p = next((x for x in tbl2._filtered if x['sku']==v2[0]), None)
                if p:
                    dlg2.price_e.delete(0,'end')
                    dlg2.price_e.insert(0, str(p['selling_price']))
        tbl2.bind_select(on_sel)

        def do_add():
            v2 = tbl2.selected_values()
            if not v2: err2.configure(text='Select a product'); return
            p  = next((x for x in tbl2._filtered if x['sku']==v2[0]), None)
            if not p: return
            try:
                qty   = int(float(dlg2.qty_e.get() or 1))
                price = float(dlg2.price_e.get() or p['selling_price'])
            except ValueError:
                err2.configure(text='Invalid qty/price'); return
            if qty <= 0:
                err2.configure(text='Qty must be > 0'); return
            if qty > p['quantity']:
                err2.configure(text=f"Only {p['quantity']} in stock"); return
            cart_tbl._items.append({
                'product_id': p['id'], 'sku': p['sku'], 'name': p['name'],
                'stock': p['quantity'], 'qty': qty,
                'unit_price': price, 'total': qty * price
            })
            self._refresh_cart(cart_tbl)
            if hasattr(cart_tbl, '_recalc'):
                cart_tbl._recalc()
            dlg2.destroy()

        tbl2.bind_double(lambda e: do_add())
        br = ctk.CTkFrame(dlg2, fg_color='transparent')
        br.pack(pady=4)
        make_green_btn(br, '+ Add to Cart', do_add, width=140).pack(side='left', padx=6)
        make_btn(br, 'Cancel', dlg2.destroy, width=90).pack(side='left')

    def _remove_item(self, cart_tbl, total_lbl, disc_e, gst_var):
        v = cart_tbl.selected_values()
        if not v: return
        cart_tbl._items = [i for i in cart_tbl._items if i['sku'] != v[0]]
        self._refresh_cart(cart_tbl)
        if hasattr(cart_tbl, '_recalc'):
            cart_tbl._recalc()

    def _refresh_cart(self, cart_tbl):
        cart_tbl.load_raw([
            (i['sku'], i['name'], i['stock'], i['qty'],
             format_currency(i['unit_price']), format_currency(i['total']))
            for i in cart_tbl._items
        ])
