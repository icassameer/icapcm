# ============================================================
#  ICA PMS — Language Strings  (English + Marathi)
# ============================================================

LANGUAGES = {"English": "en", "मराठी": "mr"}

STRINGS = {
    # ── App / Login ──────────────────────────────────────────
    "welcome":              {"en": "Welcome Back!",                         "mr": "पुन्हा स्वागत!"},
    "sign_in_sub":          {"en": "Sign in to your account",               "mr": "आपल्या खात्यात प्रवेश करा"},
    "username":             {"en": "Username",                              "mr": "वापरकर्तानाव"},
    "password":             {"en": "Password",                              "mr": "पासवर्ड"},
    "username_ph":          {"en": "Enter your username",                   "mr": "वापरकर्तानाव टाका"},
    "password_ph":          {"en": "Enter your password",                   "mr": "पासवर्ड टाका"},
    "sign_in":              {"en": "Sign In",                               "mr": "प्रवेश करा"},
    "signing_in":           {"en": "Signing in...",                         "mr": "प्रवेश होत आहे..."},
    "invalid_login":        {"en": "✖ Invalid username or password",        "mr": "✖ चुकीचे नाव किंवा पासवर्ड"},
    "enter_credentials":    {"en": "⚠ Please enter username and password",  "mr": "⚠ कृपया नाव व पासवर्ड टाका"},
    "whatsapp_support":     {"en": "WhatsApp Support",                      "mr": "व्हाट्सअॅप सहाय्य"},
    "demo_version":         {"en": "DEMO VERSION",                          "mr": "डेमो आवृत्ती"},
    "days_remaining":       {"en": "days remaining",                        "mr": "दिवस शिल्लक"},
    "last_day_warning":     {"en": "⚠ LAST DAY — Purchase full version today!", "mr": "⚠ शेवटचा दिवस — आज पूर्ण आवृत्ती खरेदी करा!"},
    "demo_expires_in":      {"en": "⏰ Demo expires in",                    "mr": "⏰ डेमो संपेल"},
    "days":                 {"en": "days",                                  "mr": "दिवसात"},
    "language":             {"en": "Language",                              "mr": "भाषा"},

    # ── Navigation ───────────────────────────────────────────
    "nav_dashboard":        {"en": "📊  Dashboard",                         "mr": "📊  मुख्यपृष्ठ"},
    "nav_products":         {"en": "📦  Products",                          "mr": "📦  उत्पादने"},
    "nav_inventory":        {"en": "🏪  Inventory",                         "mr": "🏪  साठा"},
    "nav_sales":            {"en": "💰  Sales",                             "mr": "💰  विक्री"},
    "nav_suppliers":        {"en": "🏭  Suppliers",                         "mr": "🏭  पुरवठादार"},
    "nav_reports":          {"en": "📈  Reports",                           "mr": "📈  अहवाल"},
    "nav_users":            {"en": "👥  Users",                             "mr": "👥  वापरकर्ते"},
    "nav_backup":           {"en": "🛡  Backup & Restore",                  "mr": "🛡  बॅकअप"},
    "logout":               {"en": "⎋  Logout",                            "mr": "⎋  बाहेर पडा"},

    # ── Dashboard ────────────────────────────────────────────
    "total_products":       {"en": "Total Products",                        "mr": "एकूण उत्पादने"},
    "low_stock":            {"en": "Low Stock",                             "mr": "कमी साठा"},
    "todays_sales":         {"en": "Today's Sales",                         "mr": "आजची विक्री"},
    "monthly_revenue":      {"en": "Monthly Revenue",                       "mr": "मासिक उत्पन्न"},
    "total_suppliers":      {"en": "Total Suppliers",                       "mr": "एकूण पुरवठादार"},
    "out_of_stock":         {"en": "Out of Stock",                          "mr": "साठा संपला"},

    # ── Products ─────────────────────────────────────────────
    "product_mgmt":         {"en": "📦  Product Management",                "mr": "📦  उत्पादन व्यवस्थापन"},
    "add_product":          {"en": "+ Add Product",                         "mr": "+ उत्पादन जोडा"},
    "edit_product":         {"en": "✏ Edit",                                "mr": "✏ बदला"},
    "delete_product":       {"en": "🗑 Delete",                             "mr": "🗑 हटवा"},
    "product_name":         {"en": "Product Name *",                        "mr": "उत्पादनाचे नाव *"},
    "sku":                  {"en": "SKU *",                                 "mr": "SKU *"},
    "barcode":              {"en": "Barcode",                               "mr": "बारकोड"},
    "category":             {"en": "Category",                              "mr": "प्रकार"},
    "supplier":             {"en": "Supplier",                              "mr": "पुरवठादार"},
    "cost_price":           {"en": "Cost Price (₹) *",                      "mr": "खरेदी किंमत (₹) *"},
    "selling_price":        {"en": "Selling Price (₹) *",                   "mr": "विक्री किंमत (₹) *"},
    "quantity":             {"en": "Quantity",                              "mr": "प्रमाण"},
    "min_stock_level":      {"en": "Min Stock Level",                       "mr": "किमान साठा"},
    "unit":                 {"en": "Unit",                                  "mr": "एकक"},
    "description":          {"en": "Description",                           "mr": "वर्णन"},
    "all":                  {"en": "All",                                   "mr": "सर्व"},
    "low_stock_only":       {"en": "Low Stock Only",                        "mr": "फक्त कमी साठा"},
    "search_ph":            {"en": "Search name, SKU or barcode...",        "mr": "नाव, SKU किंवा बारकोड शोधा..."},
    "opening_qty":          {"en": "Opening Qty",                           "mr": "प्रारंभिक प्रमाण"},
    "batch_no":             {"en": "Batch No",                              "mr": "बॅच क्र."},
    "expiry_date":          {"en": "Expiry Date (YYYY-MM-DD)",              "mr": "कालबाह्य तारीख (YYYY-MM-DD)"},

    # ── Inventory ────────────────────────────────────────────
    "inventory_mgmt":       {"en": "🏪  Inventory Management",              "mr": "🏪  साठा व्यवस्थापन"},
    "stock_in":             {"en": "📥 Stock In",                           "mr": "📥 साठा आला"},
    "stock_out":            {"en": "📤 Stock Out",                          "mr": "📤 साठा गेला"},
    "adjustment":           {"en": "🔧 Adjustment",                         "mr": "🔧 समायोजन"},
    "all_transactions":     {"en": "All",                                   "mr": "सर्व"},
    "low_stock_tab":        {"en": "⚠ Low Stock",                          "mr": "⚠ कमी साठा"},

    # ── Sales ────────────────────────────────────────────────
    "sales_invoices":       {"en": "💰  Sales & Invoices",                  "mr": "💰  विक्री व पावत्या"},
    "new_sale":             {"en": "+ New Sale",                            "mr": "+ नवीन विक्री"},
    "invoice_no":           {"en": "Invoice No",                            "mr": "पावती क्र."},
    "customer":             {"en": "Customer Name",                         "mr": "ग्राहकाचे नाव"},
    "walk_in":              {"en": "Walk-in",                               "mr": "थेट ग्राहक"},
    "discount":             {"en": "Discount (₹)",                          "mr": "सूट (₹)"},
    "net_total":            {"en": "NET TOTAL",                             "mr": "एकूण रक्कम"},
    "payment_method":       {"en": "Payment Method",                        "mr": "पेमेंट पद्धत"},
    "save_invoice":         {"en": "💾 Save Invoice",                       "mr": "💾 पावती जतन करा"},
    "add_to_cart":          {"en": "+ Add Product",                         "mr": "+ उत्पादन जोडा"},
    "remove":               {"en": "🗑 Remove",                             "mr": "🗑 काढा"},
    "cart_items":           {"en": "Cart Items",                            "mr": "कार्ट वस्तू"},
    "create_new_sale":      {"en": "🧾  Create New Sale",                   "mr": "🧾  नवीन विक्री तयार करा"},
    "notes":                {"en": "Notes",                                 "mr": "नोंद"},

    # ── Suppliers ────────────────────────────────────────────
    "suppliers_title":      {"en": "🏭  Suppliers, Buyers & Categories",    "mr": "🏭  पुरवठादार, खरेदीदार व प्रकार"},
    "suppliers_tab":        {"en": "🏭 Suppliers",                          "mr": "🏭 पुरवठादार"},
    "buyers_tab":           {"en": "👤 Buyers / Customers",                 "mr": "👤 खरेदीदार / ग्राहक"},
    "categories_tab":       {"en": "🏷 Categories",                         "mr": "🏷 प्रकार"},
    "add_supplier":         {"en": "+ Add Supplier",                        "mr": "+ पुरवठादार जोडा"},
    "add_buyer":            {"en": "+ Add Buyer",                           "mr": "+ खरेदीदार जोडा"},
    "add_category":         {"en": "+ Add Category",                        "mr": "+ प्रकार जोडा"},

    # ── Reports ──────────────────────────────────────────────
    "reports_title":        {"en": "📈  Reports & Analytics",               "mr": "📈  अहवाल व विश्लेषण"},
    "export_excel":         {"en": "📊 Export Excel",                       "mr": "📊 Excel निर्यात"},
    "export_pdf":           {"en": "📄 Export PDF",                         "mr": "📄 PDF निर्यात"},

    # ── Users ────────────────────────────────────────────────
    "user_mgmt":            {"en": "👥  User Management",                   "mr": "👥  वापरकर्ता व्यवस्थापन"},
    "add_user":             {"en": "+ Add User",                            "mr": "+ वापरकर्ता जोडा"},
    "full_name":            {"en": "Full Name",                             "mr": "पूर्ण नाव"},
    "role":                 {"en": "Role",                                  "mr": "भूमिका"},

    # ── Backup ───────────────────────────────────────────────
    "backup_title":         {"en": "🛡  Backup & Restore",                  "mr": "🛡  बॅकअप व पुनर्संचय"},
    "create_backup":        {"en": "💾 Create Backup",                      "mr": "💾 बॅकअप तयार करा"},
    "restore_backup":       {"en": "📂 Restore Backup",                     "mr": "📂 बॅकअप पुनर्संचय"},

    # ── Common buttons/labels ────────────────────────────────
    "save":                 {"en": "💾 Save",                               "mr": "💾 जतन करा"},
    "cancel":               {"en": "Cancel",                                "mr": "रद्द करा"},
    "delete":               {"en": "🗑 Delete",                             "mr": "🗑 हटवा"},
    "edit":                 {"en": "✏ Edit",                                "mr": "✏ बदला"},
    "search_btn":           {"en": "🔍 Filter",                             "mr": "🔍 गाळण"},
    "from_date":            {"en": "From:",                                 "mr": "पासून:"},
    "to_date":              {"en": "To:",                                   "mr": "पर्यंत:"},
    "today":                {"en": "Today",                                 "mr": "आज"},
    "week":                 {"en": "Week",                                  "mr": "आठवडा"},
    "month":                {"en": "Month",                                 "mr": "महिना"},
    "status":               {"en": "Status",                                "mr": "स्थिती"},
    "date":                 {"en": "Date",                                  "mr": "तारीख"},
    "name":                 {"en": "Name",                                  "mr": "नाव"},
    "phone":                {"en": "Phone",                                 "mr": "फोन"},
    "email":                {"en": "Email",                                 "mr": "ईमेल"},
    "address":              {"en": "Address",                               "mr": "पत्ता"},
    "select_first":         {"en": "Please select a row first.",            "mr": "कृपया प्रथम एक ओळ निवडा."},
    "admin_only":           {"en": "Only Admin can perform this action.",   "mr": "फक्त प्रशासक हे करू शकतो."},
    "go_to_page":           {"en": "Go to page:",                           "mr": "पृष्ठावर जा:"},
    "rows_per_page":        {"en": "Rows/page:",                            "mr": "ओळी/पृष्ठ:"},
    "showing":              {"en": "Showing",                               "mr": "दाखवत आहे"},
    "of":                   {"en": "of",                                    "mr": "पैकी"},
    "page":                 {"en": "Page",                                  "mr": "पृष्ठ"},
}

# ── Global language state ─────────────────────────────────────
_current = "en"

def set_lang(code: str):
    global _current
    _current = code

def get_lang() -> str:
    return _current

def t(key: str) -> str:
    """Return translated string for current language."""
    row = STRINGS.get(key)
    if not row:
        return key
    return row.get(_current) or row.get("en") or key
