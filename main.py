import sqlite3
import json
from datetime import datetime, timedelta
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, ScreenManager
from kivymd.uix.card import MDCard
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton, MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import TwoLineAvatarIconListItem, IconLeftWidget, OneLineAvatarIconListItem, IconRightWidget
from kivy.properties import StringProperty, NumericProperty, ObjectProperty, ListProperty
from kivy.core.window import Window

# --- AJUSTE DE PANTALLA V18 ---
# Eliminamos la restricción de tamaño para que se adapte al celular
# Window.size = (360, 640) 

# --- BASE DE DATOS ---
class Database:
    def __init__(self):
        # V18: Ajuste de menús anchos y pantalla completa
        self.conn = sqlite3.connect("pollos_rrj_v18.db", check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT,
                details TEXT,
                price REAL,
                status TEXT, 
                payment_method TEXT,
                date_created TEXT, 
                date_paid TEXT,
                delivery_type TEXT,
                moto_price REAL,
                cart_json TEXT
            )
        """)
        self.conn.commit()

    def add_order(self, name, details, price, delivery, moto, cart_data):
        date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cart_str = json.dumps(cart_data) 
        self.cursor.execute("""
            INSERT INTO orders (customer_name, details, price, status, payment_method, date_created, 
                                delivery_type, moto_price, cart_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, details, price, "ACTIVO", "PENDIENTE", date_now, delivery, moto, cart_str))
        self.conn.commit()

    def update_order(self, order_id, name, details, price, delivery, moto, cart_data):
        cart_str = json.dumps(cart_data)
        self.cursor.execute("""
            UPDATE orders SET 
                customer_name=?, details=?, price=?, delivery_type=?, moto_price=?, cart_json=?
            WHERE id=?
        """, (name, details, price, delivery, moto, cart_str, order_id))
        self.conn.commit()

    def delete_order(self, order_id):
        self.cursor.execute("DELETE FROM orders WHERE id=?", (order_id,))
        self.conn.commit()
        
    def clear_all_delivered(self):
        self.cursor.execute("DELETE FROM orders WHERE status='ENTREGADO'")
        self.conn.commit()

    def get_order_by_id(self, oid):
        self.cursor.execute("SELECT * FROM orders WHERE id=?", (oid,))
        return self.cursor.fetchone()

    def get_active_orders(self):
        self.cursor.execute("SELECT * FROM orders WHERE status='ACTIVO'")
        return self.cursor.fetchall()

    def get_orders_by_status(self, status):
        self.cursor.execute("SELECT * FROM orders WHERE status=? ORDER BY date_created DESC", (status,))
        return self.cursor.fetchall()

    def get_report_data(self):
        self.cursor.execute("SELECT * FROM orders WHERE status='ENTREGADO' ORDER BY date_paid DESC")
        return self.cursor.fetchall()

    def mark_delivered(self, order_id, payment_method):
        status = "ENTREGADO"
        date_p = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if payment_method == "FIADO":
            status = "FIADO"
            date_p = None 
        self.cursor.execute("""
            UPDATE orders SET status=?, payment_method=?, date_paid=? WHERE id=?
        """, (status, payment_method, date_p, order_id))
        self.conn.commit()

    def pay_credit_order(self, order_id, payment_method):
        date_p = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("""
            UPDATE orders SET status='ENTREGADO', payment_method=?, date_paid=? WHERE id=?
        """, (payment_method, date_p, order_id))
        self.conn.commit()

db = Database()

# --- INTERFAZ (KV) ---
KV = '''
<DeleteDialogContent>:
    orientation: "vertical"
    size_hint_y: None
    height: "140dp"
    spacing: "15dp"
    padding: "10dp"

    MDLabel:
        text: "¿Qué deseas hacer?"
        halign: "center"
        bold: True
        theme_text_color: "Primary"
        size_hint_y: None
        height: "30dp"

    MDBoxLayout:
        orientation: "horizontal"
        spacing: "10dp"
        adaptive_height: True
        pos_hint: {"center_x": 0.5}
        
        MDRaisedButton:
            text: "SELECCIONAR"
            md_bg_color: 0.2, 0.4, 0.8, 1
            on_release: root.select_action()
            
        MDRaisedButton:
            text: "BORRAR TODO"
            md_bg_color: 0.8, 0, 0, 1
            on_release: root.delete_all_action()

    MDRaisedButton:
        text: "CANCELAR"
        md_bg_color: 0.5, 0.5, 0.5, 1
        pos_hint: {"center_x": 0.5}
        on_release: root.cancel_action()

<HistoryMenuScreen>:
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: 0.98, 0.98, 0.98, 1
        MDTopAppBar:
            title: "Gestión y Reportes"
            md_bg_color: 1, 0.5, 0, 1
            left_action_items: [["arrow-left", lambda x: app.go_home()]]
        MDBoxLayout:
            orientation: "vertical"
            padding: "20dp"
            spacing: "20dp"
            adaptive_height: True
            pos_hint: {"top": 1}
            MDRaisedButton:
                text: "PEDIDOS ENTREGADOS"
                font_size: "18sp"
                size_hint_x: 0.9
                height: "80dp"
                pos_hint: {"center_x": 0.5}
                md_bg_color: 0.2, 0.6, 0.2, 1
                on_release: app.go_to_delivered()
            MDRaisedButton:
                text: "PEDIDOS FIADOS"
                font_size: "18sp"
                size_hint_x: 0.9
                height: "80dp"
                pos_hint: {"center_x": 0.5}
                md_bg_color: 0.8, 0.2, 0.2, 1
                on_release: app.go_to_credit()
            MDRaisedButton:
                text: "HISTORIAL (BÚSQUEDA)"
                font_size: "18sp"
                size_hint_x: 0.9
                height: "80dp"
                pos_hint: {"center_x": 0.5}
                md_bg_color: 0.2, 0.4, 0.8, 1
                on_release: app.go_to_report()
        Widget:

<OrderListScreen>:
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: 0.95, 0.95, 0.95, 1
        
        MDTopAppBar:
            id: toolbar
            title: "Lista"
            md_bg_color: 1, 0.5, 0, 1
            left_action_items: [["arrow-left", lambda x: app.go_to_history_menu()]]
            right_action_items: []

        MDScrollView:
            MDList:
                id: the_list

    MDFloatingActionButton:
        id: fab_delete
        icon: "trash-can"
        md_bg_color: 0.8, 0, 0, 1
        pos_hint: {"right": 0.95, "y": 0.05}
        disabled: True
        opacity: 0
        on_release: root.delete_selected_items()

<ReportScreen>:
    lbl_result: lbl_result
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: 1, 1, 1, 1
        MDTopAppBar:
            id: toolbar
            title: "Buscador Historial"
            md_bg_color: 1, 0.5, 0, 1
            left_action_items: [["arrow-left", lambda x: app.go_to_history_menu()]]
            
        MDBoxLayout:
            orientation: "vertical"
            padding: "20dp"
            spacing: "15dp"
            adaptive_height: True
            
            MDLabel:
                text: "FILTROS DE BÚSQUEDA"
                halign: "center"
                bold: True
            
            MDRectangleFlatButton:
                id: btn_filter
                text: "Filtro Rápido: Ninguno"
                size_hint_x: 1
                text_color: 0,0,0,1
                on_release: root.open_menu('filter')

            MDBoxLayout:
                orientation: "horizontal"
                spacing: "10dp"
                adaptive_height: True
                MDRectangleFlatButton:
                    id: btn_day
                    text: "Día: Todos"
                    size_hint_x: 0.3
                    on_release: root.open_menu('day')
                MDRectangleFlatButton:
                    id: btn_month
                    text: "Mes: Todos"
                    size_hint_x: 0.4
                    on_release: root.open_menu('month')
                MDRectangleFlatButton:
                    id: btn_year
                    text: "Año: 2026"
                    size_hint_x: 0.3
                    on_release: root.open_menu('year')

            MDRaisedButton:
                text: "BUSCAR / CALCULAR"
                size_hint_x: 1
                md_bg_color: 1, 0.5, 0, 1
                on_release: root.generate_report()
            
            MDCard:
                size_hint_y: None
                height: "80dp"
                md_bg_color: 0.9, 1, 0.9, 1
                padding: "10dp"
                MDLabel:
                    id: lbl_result
                    text: "TOTAL: 0 Bs"
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: 0, 0.5, 0, 1
                    font_style: "H4"
                    bold: True
        
        MDScrollView:
            MDList:
                id: report_list

    MDFloatingActionButton:
        id: fab_delete_rep
        icon: "trash-can"
        md_bg_color: 0.8, 0, 0, 1
        pos_hint: {"right": 0.95, "y": 0.05}
        disabled: True
        opacity: 0
        on_release: root.delete_selected_items()

<DetailDialogContent>:
    orientation: "vertical"
    spacing: "5dp"
    size_hint_y: None
    height: "480dp"
    MDLabel:
        text: root.title_txt
        halign: "center"
        bold: True
        font_style: "H6"
        size_hint_y: None
        height: "30dp"
    MDLabel:
        text: root.date_txt
        halign: "center"
        font_style: "Caption"
        size_hint_y: None
        height: "20dp"
    MDScrollView:
        MDBoxLayout:
            orientation: "vertical"
            adaptive_height: True
            padding: "10dp"
            MDLabel:
                text: root.details_txt
                markup: True
                theme_text_color: "Primary"
                adaptive_height: True
    MDBoxLayout:
        size_hint_y: None
        height: "40dp"
        md_bg_color: 0.9, 0.9, 0.9, 1
        padding: "10dp"
        MDLabel:
            text: "TOTAL:"
            bold: True
        MDLabel:
            text: root.total_txt
            halign: "right"
            bold: True
            theme_text_color: "Error"
            font_style: "H6"
    MDBoxLayout:
        id: action_area
        orientation: "vertical"
        size_hint_y: None
        height: "100dp"
        spacing: "5dp"
        padding: "5dp"

<PaymentDialogContent>:
    orientation: "vertical"
    spacing: "10dp"
    size_hint_y: None
    height: "400dp"
    MDLabel:
        text: "DETALLE DE LA CUENTA"
        halign: "center"
        bold: True
        theme_text_color: "Custom"
        text_color: 1, 0.5, 0, 1
        font_style: "H6"
        size_hint_y: None
        height: "30dp"
    MDScrollView:
        MDBoxLayout:
            orientation: "vertical"
            adaptive_height: True
            padding: "10dp"
            MDLabel:
                text: root.details_text
                markup: True
                halign: "left"
                theme_text_color: "Primary"
                font_style: "Body1"
                adaptive_height: True
    MDBoxLayout:
        size_hint_y: None
        height: "40dp"
        md_bg_color: 0.9, 0.9, 0.9, 1
        padding: "10dp"
        radius: [10,]
        MDLabel:
            text: "TOTAL A PAGAR:"
            bold: True
        MDLabel:
            text: root.total_text
            halign: "right"
            bold: True
            theme_text_color: "Error"
            font_style: "H5"
    MDGridLayout:
        cols: 3
        spacing: "10dp"
        size_hint_y: None
        height: "60dp"
        MDRaisedButton:
            text: "FIADO"
            md_bg_color: 0.8, 0, 0, 1
            size_hint_x: 1
            on_release: root.pay("FIADO")
        MDRaisedButton:
            text: "QR"
            md_bg_color: 0, 0.5, 0.8, 1
            size_hint_x: 1
            on_release: root.pay("QR")
        MDRaisedButton:
            text: "EFECTIVO"
            md_bg_color: 0, 0.6, 0.2, 1
            size_hint_x: 1
            on_release: root.pay("EFECTIVO")
    MDRaisedButton:
        text: "CANCELAR / CERRAR"
        md_bg_color: 0.5, 0.5, 0.5, 1
        size_hint_x: 0.8
        pos_hint: {"center_x": 0.5}
        on_release: root.cancel()

<OrderCard>:
    orientation: "vertical"
    size_hint_y: None
    height: "340dp" 
    padding: "0dp"
    elevation: 3
    radius: [15, 15, 15, 15]
    md_bg_color: 1, 1, 1, 1
    MDBoxLayout:
        size_hint_y: 0.2
        md_bg_color: 1, 0.5, 0, 1
        radius: [15, 15, 0, 0]
        padding: "10dp"
        MDLabel:
            text: root.customer_name
            halign: "center"
            bold: True
            theme_text_color: "Custom"
            text_color: 1,1,1,1
            font_style: "H5"
    MDBoxLayout:
        orientation: "vertical"
        padding: "10dp"
        spacing: "5dp"
        MDScrollView:
            size_hint_y: 0.55
            MDLabel:
                text: root.order_details
                halign: "center"
                theme_text_color: "Primary"
                adaptive_height: True
                font_style: "H6"
                markup: True
        MDLabel:
            text: "Total: " + str(root.total_price) + " Bs"
            halign: "center"
            bold: True
            theme_text_color: "Error"
            font_style: "H5"
            size_hint_y: 0.15
        MDBoxLayout:
            orientation: "vertical"
            spacing: "8dp"
            size_hint_y: 0.35
            MDBoxLayout:
                spacing: "10dp"
                adaptive_height: True
                MDRaisedButton:
                    text: "EDITAR"
                    size_hint_x: 0.5
                    md_bg_color: 0.5, 0.5, 0.5, 1
                    on_release: app.edit_order(root.order_id)
                MDRaisedButton:
                    text: "ENTREGAR"
                    size_hint_x: 0.5
                    md_bg_color: 0.2, 0.6, 0.2, 1
                    on_release: root.open_payment_dialog()
            MDRaisedButton:
                text: "ELIMINAR"
                size_hint_x: 1
                md_bg_color: 0.8, 0.2, 0.2, 1
                on_release: app.delete_order(root.order_id)

<HomeScreen>:
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: 0.95, 0.95, 0.95, 1
        MDTopAppBar:
            title: "Pedidos Activos"
            md_bg_color: 1, 0.5, 0, 1
            right_action_items: [["chart-bar", lambda x: app.go_to_history_menu()]]
        MDScrollView:
            MDGridLayout:
                id: orders_grid
                cols: 2
                spacing: "10dp"
                padding: "10dp"
                adaptive_height: True
                row_default_height: "340dp"
                row_force_default: True
    MDFloatingActionButton:
        icon: "plus"
        md_bg_color: 1, 0.5, 0, 1
        pos_hint: {"right": 0.9, "y": 0.05}
        on_release: app.go_to_add()

<AddOrderScreen>:
    name_input: name_input
    moto_input: moto_input
    cart_list: cart_list
    lbl_total: lbl_total
    btn_qty_food: btn_qty_food
    btn_qty_soda: btn_qty_soda
    
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: 1, 1, 1, 1
        MDTopAppBar:
            id: toolbar
            title: "Nuevo Pedido"
            md_bg_color: 1, 0.5, 0, 1
            left_action_items: [["arrow-left", lambda x: app.cancel_add()]]
        MDScrollView:
            MDBoxLayout:
                orientation: "vertical"
                padding: "15dp"
                spacing: "10dp"
                adaptive_height: True
                alignment: "center"
                MDLabel:
                    text: "CLIENTE Y ENTREGA"
                    halign: "center"
                    bold: True
                    theme_text_color: "Custom"
                    text_color: 1, 0.5, 0, 1
                    font_style: "Subtitle2"
                MDTextField:
                    id: name_input
                    hint_text: "Nombre del Cliente"
                    mode: "rectangle"
                    size_hint_x: 0.9
                    pos_hint: {"center_x": 0.5}
                    text_color_normal: 0, 0, 0, 1
                    text_color_focus: 0, 0, 0, 1
                MDBoxLayout:
                    orientation: "horizontal"
                    spacing: "10dp"
                    size_hint_x: 0.9
                    pos_hint: {"center_x": 0.5}
                    adaptive_height: True
                    MDRectangleFlatButton:
                        id: btn_delivery
                        text: "Para Mesa"
                        size_hint_x: 0.5
                        text_color: 0,0,0,1
                        on_release: root.open_menu('delivery')
                    MDTextField:
                        id: moto_input
                        hint_text: "Costo Moto"
                        mode: "rectangle"
                        input_filter: "float"
                        size_hint_x: 0.5
                        disabled: True
                        opacity: 0
                        text_color_normal: 0, 0, 0, 1
                        text_color_focus: 0, 0, 0, 1
                MDBoxLayout:
                    size_hint_y: None
                    height: "1dp"
                    md_bg_color: 0.9, 0.9, 0.9, 1
                MDLabel:
                    text: "COMIDA PRINCIPAL"
                    halign: "center"
                    bold: True
                    theme_text_color: "Custom"
                    text_color: 1, 0.5, 0, 1
                    font_style: "Subtitle2"
                MDBoxLayout:
                    orientation: "horizontal"
                    spacing: "10dp"
                    size_hint_x: 0.9
                    pos_hint: {"center_x": 0.5}
                    adaptive_height: True
                    MDRectangleFlatButton:
                        id: btn_food
                        text: "Pollo Broaster"
                        size_hint_x: 0.7
                        text_color: 0,0,0,1
                        on_release: root.open_menu('food')
                    MDRectangleFlatButton:
                        id: btn_qty_food
                        text: "1"
                        size_hint_x: 0.3
                        text_color: 0,0,0,1
                        on_release: root.open_qty_menu('food')
                MDLabel:
                    text: "DETALLES (Presa / Guarnición)"
                    halign: "center"
                    bold: True
                    theme_text_color: "Custom"
                    text_color: 1, 0.5, 0, 1
                    font_style: "Subtitle2"
                MDGridLayout:
                    cols: 2
                    spacing: "10dp"
                    size_hint_x: 0.9
                    pos_hint: {"center_x": 0.5}
                    adaptive_height: True
                    MDRectangleFlatButton:
                        id: btn_cut
                        text: "Pierna"
                        size_hint_x: 1
                        text_color: 0,0,0,1
                        on_release: root.open_menu('cut')
                    MDRectangleFlatButton:
                        id: btn_variant
                        text: "Normal (Arroz y Papa)"
                        size_hint_x: 1
                        text_color: 0,0,0,1
                        on_release: root.open_menu('variant')
                MDLabel:
                    text: "BEBIDA / SODA"
                    halign: "center"
                    bold: True
                    theme_text_color: "Custom"
                    text_color: 1, 0.5, 0, 1
                    font_style: "Subtitle2"
                MDBoxLayout:
                    orientation: "horizontal"
                    spacing: "10dp"
                    size_hint_x: 0.9
                    pos_hint: {"center_x": 0.5}
                    adaptive_height: True
                    MDRectangleFlatButton:
                        id: btn_soda
                        text: "Ninguna"
                        size_hint_x: 0.7
                        pos_hint: {"center_x": 0.5}
                        text_color: 0,0,0,1
                        on_release: root.open_menu('soda')
                    MDRectangleFlatButton:
                        id: btn_qty_soda
                        text: "1"
                        size_hint_x: 0.3
                        text_color: 0,0,0,1
                        on_release: root.open_qty_menu('soda')
                Widget:
                    size_hint_y: None
                    height: "10dp"
                MDRaisedButton:
                    text: "AGREGAR AL CARRITO (+)"
                    size_hint_x: 0.9
                    pos_hint: {"center_x": 0.5}
                    md_bg_color: 0.2, 0.6, 0.8, 1
                    on_release: root.add_item_to_cart()
                MDBoxLayout:
                    orientation: "vertical"
                    size_hint_y: None
                    adaptive_height: True
                    md_bg_color: 0.95, 0.95, 0.95, 1
                    radius: [10,]
                    padding: "5dp"
                    MDLabel:
                        text: "RESUMEN DEL PEDIDO:"
                        font_style: "Caption"
                        halign: "center"
                    MDList:
                        id: cart_list
                    MDLabel:
                        id: lbl_total
                        text: "TOTAL: 0 Bs"
                        halign: "right"
                        bold: True
                        font_style: "H6"
                        theme_text_color: "Error"
                        padding_x: "20dp"
                Widget:
                    size_hint_y: None
                    height: "20dp"
                MDRaisedButton:
                    id: save_btn
                    text: "GUARDAR PEDIDO COMPLETO"
                    size_hint_x: 1
                    height: "60dp"
                    md_bg_color: 1, 0.5, 0, 1
                    font_size: "18sp"
                    on_release: root.save_order_final()
'''

# --- LÓGICA ---

class DetailDialogContent(MDBoxLayout):
    title_txt = StringProperty("")
    date_txt = StringProperty("")
    details_txt = StringProperty("")
    total_txt = StringProperty("")

class PaymentDialogContent(MDBoxLayout):
    details_text = StringProperty("")
    total_text = StringProperty("")
    order_card = ObjectProperty(None)
    def pay(self, method): self.order_card.process_payment(method)
    def cancel(self): self.order_card.dialog.dismiss()

class DeleteDialogContent(MDBoxLayout):
    screen = ObjectProperty(None)
    dialog = ObjectProperty(None)
    def select_action(self):
        self.dialog.dismiss()
        self.screen.start_selection_mode()
    def delete_all_action(self):
        self.dialog.dismiss()
        self.screen.confirm_delete_all()
    def cancel_action(self):
        self.dialog.dismiss()

class OrderCard(MDCard):
    order_id = NumericProperty(0)
    customer_name = StringProperty("")
    order_details = StringProperty("")
    total_price = NumericProperty(0)
    dialog = None
    
    def open_payment_dialog(self):
        content = PaymentDialogContent()
        content.details_text = self.order_details
        content.total_text = f"{self.total_price} Bs"
        content.order_card = self
        self.dialog = MDDialog(type="custom", content_cls=content)
        self.dialog.open()

    def process_payment(self, method):
        db.mark_delivered(self.order_id, method)
        if self.dialog: self.dialog.dismiss()
        app = MDApp.get_running_app()
        app.refresh_home()

# PANTALLA MENÚ HISTORIAL
class HistoryMenuScreen(Screen):
    pass

# PANTALLA LISTA GENERICA (Para Entregados y Fiados)
class OrderListScreen(Screen):
    mode = "delivered" 
    selection_mode = False
    selected_ids = []
    
    def on_enter(self):
        self.exit_selection_mode()
        self.load_data()
        
    def load_data(self):
        self.ids.the_list.clear_widgets()
        app = MDApp.get_running_app()
        
        if self.selection_mode:
            self.ids.toolbar.title = f"Selec: {len(self.selected_ids)}"
            self.ids.toolbar.left_action_items = [["close", lambda x: self.exit_selection_mode()]]
            self.ids.toolbar.right_action_items = []
            self.ids.fab_delete.disabled = False
            self.ids.fab_delete.opacity = 1
        else:
            self.ids.toolbar.left_action_items = [["arrow-left", lambda x: app.go_to_history_menu()]]
            self.ids.fab_delete.disabled = True
            self.ids.fab_delete.opacity = 0
            
            if self.mode == "delivered":
                self.ids.toolbar.title = "Pedidos Entregados"
                self.ids.toolbar.right_action_items = [["trash-can", lambda x: self.ask_delete_mode()]]
                orders = db.get_orders_by_status("ENTREGADO")
                icon_n = "check-circle"
                col = (0, 0.6, 0, 1)
            else:
                self.ids.toolbar.title = "Fiados (Por Cobrar)"
                self.ids.toolbar.right_action_items = [] 
                orders = db.get_orders_by_status("FIADO")
                icon_n = "alert-circle"
                col = (1, 0, 0, 1)

        if not self.selection_mode:
            for o in orders:
                oid, name, price, date = o[0], o[1], o[3], o[6]
                if self.mode == "delivered" and o[7]: date = o[7] 
                item = TwoLineAvatarIconListItem(
                    text=f"{name} - {price} Bs",
                    secondary_text=f"{date}",
                    on_release=lambda x, order=o: self.show_details(order)
                )
                item.add_widget(IconLeftWidget(icon=icon_n, theme_text_color="Custom", text_color=col))
                self.ids.the_list.add_widget(item)
        else:
            orders = db.get_orders_by_status("ENTREGADO" if self.mode=="delivered" else "FIADO")
            for o in orders:
                oid = o[0]
                is_selected = oid in self.selected_ids
                icon_n = "checkbox-marked" if is_selected else "checkbox-blank-outline"
                item = TwoLineAvatarIconListItem(
                    text=f"{o[1]} - {o[3]} Bs",
                    secondary_text=f"{o[6]}",
                    on_release=lambda x, order_id=oid: self.toggle_selection(order_id)
                )
                item.add_widget(IconLeftWidget(icon=icon_n, theme_text_color="Custom", text_color=(0,0,0,1)))
                self.ids.the_list.add_widget(item)

    def ask_delete_mode(self):
        content = DeleteDialogContent()
        content.screen = self
        self.dialog_del = MDDialog(type="custom", content_cls=content)
        content.dialog = self.dialog_del
        self.dialog_del.open()

    def start_selection_mode(self):
        self.selection_mode = True
        self.selected_ids = []
        self.load_data()

    def exit_selection_mode(self):
        self.selection_mode = False
        self.selected_ids = []
        self.load_data()

    def toggle_selection(self, oid):
        if oid in self.selected_ids: self.selected_ids.remove(oid)
        else: self.selected_ids.append(oid)
        self.load_data()

    def delete_selected_items(self):
        if not self.selected_ids: return
        for oid in self.selected_ids: db.delete_order(oid)
        self.exit_selection_mode()

    def confirm_delete_all(self):
        d2 = MDDialog(
            title="¿ESTÁS SEGURO?",
            text="Se borrarán TODOS los pedidos entregados.",
            buttons=[
                MDFlatButton(text="NO", on_release=lambda x: d2.dismiss()),
                MDRaisedButton(text="SÍ, BORRAR", md_bg_color=(1,0,0,1), on_release=lambda x: self.do_clear_all(d2))
            ]
        )
        d2.open()

    def do_clear_all(self, dialog):
        db.clear_all_delivered()
        dialog.dismiss()
        self.load_data()

    def show_details(self, order):
        oid, name, details, price, status, pay_method, date_created, date_paid = order[0], order[1], order[2], order[3], order[4], order[5], order[6], order[7]
        
        pretty_details = ""
        cart_json = order[10]
        try:
            cart = json.loads(cart_json)
            for item in cart:
                pretty_details += f"[b]{item['qty']}x[/b] {item['desc']} - {item['price']} Bs\n"
            if order[9] and order[9] > 0: pretty_details += f"Moto: {order[9]} Bs\n"
        except: pretty_details = details

        content = DetailDialogContent()
        content.title_txt = name
        content.date_txt = f"Pedido: {date_created}\nEstado: DEBE" if status == "FIADO" else f"Pagado: {date_paid}\n({pay_method})"
        content.details_txt = pretty_details
        content.total_txt = f"{price} Bs"
        
        layout = content.ids.action_area
        self.dialog = MDDialog(type="custom", content_cls=content)

        if status == "FIADO":
            # Botones centrados
            box = MDBoxLayout(orientation="horizontal", spacing="10dp", adaptive_size=True, pos_hint={"center_x": 0.5})
            box.add_widget(MDRaisedButton(text="PAGADO", md_bg_color=(0,0.6,0.2,1), on_release=lambda x: self.prompt_payment_method(oid)))
            box.add_widget(MDRaisedButton(text="ELIMINAR", md_bg_color=(0.8,0.2,0.2,1), on_release=lambda x: self.delete_and_refresh(oid)))
            layout.add_widget(box)
            layout.add_widget(MDRaisedButton(text="CANCELAR", md_bg_color=(0.5,0.5,0.5,1), size_hint_x=0.8, pos_hint={"center_x": 0.5}, on_release=lambda x: self.dialog.dismiss()))
        else:
            layout.add_widget(MDRaisedButton(text="CERRAR", md_bg_color=(0.5,0.5,0.5,1), size_hint_x=0.8, pos_hint={"center_x": 0.5}, on_release=lambda x: self.dialog.dismiss()))
            
        self.dialog.open()

    def delete_and_refresh(self, oid):
        db.delete_order(oid)
        self.dialog.dismiss()
        self.load_data()

    def prompt_payment_method(self, oid):
        self.dialog.dismiss()
        content = MDBoxLayout(orientation="vertical", size_hint_y=None, height="120dp", spacing="10dp", padding="10dp")
        row = MDBoxLayout(orientation="horizontal", spacing="10dp", adaptive_size=True, pos_hint={"center_x": 0.5})
        row.add_widget(MDRaisedButton(text="EFECTIVO", md_bg_color=(0,0.6,0.2,1), on_release=lambda x: self.pay_confirm(oid, "EFECTIVO")))
        row.add_widget(MDRaisedButton(text="QR", md_bg_color=(0,0.5,0.8,1), on_release=lambda x: self.pay_confirm(oid, "QR")))
        content.add_widget(row)
        content.add_widget(MDRaisedButton(text="CANCELAR", size_hint_x=0.8, pos_hint={"center_x":0.5}, md_bg_color=(0.5,0.5,0.5,1), on_release=lambda x: self.pay_dialog.dismiss()))
        
        self.pay_dialog = MDDialog(title="¿Cómo pagó?", type="custom", content_cls=content)
        self.pay_dialog.open()

    def pay_confirm(self, oid, method):
        db.pay_credit_order(oid, method)
        self.pay_dialog.dismiss()
        self.load_data() 

# PANTALLA REPORTES
class ReportScreen(Screen):
    sel_filter = "Ninguno"
    sel_day = "Todos"; sel_month = "Todos"; sel_year = "2026"; menus = {}
    selection_mode = False; selected_ids = []

    def on_enter(self): 
        if not self.menus: self.create_menus()
        self.exit_selection_mode()
        
    def create_menus(self):
        filters = ["Ninguno", "Hoy", "Última Semana", "Último Mes", "Último Año"]
        days = ["Todos"] + [str(i) for i in range(1, 32)]
        months = ["Todos", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
        years = ["2026", "2027", "2028", "2029", "2030"]
        
        self.menus['filter'] = self._make(filters, self.ids.btn_filter, 'sel_filter')
        self.menus['day'] = self._make(days, self.ids.btn_day, 'sel_day')
        self.menus['month'] = self._make(months, self.ids.btn_month, 'sel_month')
        self.menus['year'] = self._make(years, self.ids.btn_year, 'sel_year')

    def _make(self, items, btn, var):
        # Aumentamos width_mult a 5 para que quepa texto largo en el menú
        return MDDropdownMenu(caller=btn, items=[{"text": i, "viewclass": "OneLineListItem", "on_release": lambda x=i: self.set_val(x, btn, var)} for i in items], width_mult=5, max_height=300)

    def set_val(self, txt, btn, var):
        setattr(self, var, txt)
        # Lógica de Bloqueo por Filtro Rapido
        if var == 'sel_filter':
            if txt != "Ninguno":
                self.ids.btn_day.disabled = True
                self.ids.btn_month.disabled = True
                self.ids.btn_year.disabled = True
                self.ids.btn_day.text = "---"
                self.ids.btn_month.text = "---"
                self.ids.btn_year.text = "---"
            else:
                self.ids.btn_day.disabled = False
                self.ids.btn_month.disabled = False
                self.ids.btn_year.disabled = False
                self.ids.btn_day.text = f"Día: {self.sel_day}"
                self.ids.btn_month.text = f"Mes: {self.sel_month}"
                self.ids.btn_year.text = f"Año: {self.sel_year}"
            btn.text = f"Filtro Rápido: {txt}"
        else:
            label = var.split('_')[1].capitalize()
            btn.text = f"{label}: {txt}"
            
        self.menus[var.replace('sel_', '')].dismiss()

    def open_menu(self, key): self.menus[key].open()

    def generate_report(self):
        app = MDApp.get_running_app()
        self.exit_selection_mode()
        self.run_filter()

    def run_filter(self):
        all_orders = db.get_report_data()
        filtered = []; total = 0
        now = datetime.now()
        
        for o in all_orders:
            if not o[7]: continue 
            d_obj = datetime.strptime(o[7], "%Y-%m-%d %H:%M:%S")
            
            match = True
            # Logica Especial
            if self.sel_filter == "Hoy":
                if d_obj.date() != now.date(): match = False
            elif self.sel_filter == "Última Semana":
                if d_obj < now - timedelta(days=7): match = False
            elif self.sel_filter == "Último Mes":
                if d_obj < now - timedelta(days=30): match = False
            elif self.sel_filter == "Último Año":
                if d_obj < now - timedelta(days=365): match = False
            elif self.sel_filter == "Ninguno":
                # Logica Manual
                if str(d_obj.year) != self.sel_year: match = False
                if self.sel_month != "Todos" and f"{d_obj.month:02d}" != self.sel_month: match = False
                if self.sel_day != "Todos" and str(d_obj.day) != self.sel_day: match = False
            
            if match:
                filtered.append(o); total += o[3]

        self.ids.report_list.clear_widgets()
        self.ids.toolbar.right_action_items = [["trash-can", lambda x: self.ask_delete_mode()]]
        
        if self.selection_mode:
            self.ids.toolbar.title = f"Selec: {len(self.selected_ids)}"
            self.ids.toolbar.left_action_items = [["close", lambda x: self.exit_selection_mode()]]
            self.ids.fab_delete_rep.disabled = False; self.ids.fab_delete_rep.opacity = 1
            
            for o in filtered:
                oid = o[0]
                is_selected = oid in self.selected_ids
                icon_n = "checkbox-marked" if is_selected else "checkbox-blank-outline"
                item = TwoLineAvatarIconListItem(
                    text=f"{o[1]} - {o[3]} Bs", secondary_text=f"{o[7]}",
                    on_release=lambda x, order_id=oid: self.toggle_selection(order_id)
                )
                item.add_widget(IconLeftWidget(icon=icon_n, theme_text_color="Custom", text_color=(0,0,0,1)))
                self.ids.report_list.add_widget(item)
        else:
            app = MDApp.get_running_app()
            self.ids.toolbar.title = "Resultados"
            self.ids.toolbar.left_action_items = [["arrow-left", lambda x: app.go_to_history_menu()]]
            self.ids.fab_delete_rep.disabled = True; self.ids.fab_delete_rep.opacity = 0
            
            for o in filtered:
                item = TwoLineAvatarIconListItem(text=f"{o[1]} - {o[3]} Bs", secondary_text=f"{o[7]}", on_release=lambda x, order=o: self.show_details_report(order))
                item.add_widget(IconLeftWidget(icon="cash"))
                self.ids.report_list.add_widget(item)
                
        self.ids.lbl_result.text = f"TOTAL: {total} Bs"

    # LOGICA SELECCION REPORTE
    def ask_delete_mode(self):
        content = DeleteDialogContent()
        content.screen = self
        self.dialog_del = MDDialog(type="custom", content_cls=content)
        content.dialog = self.dialog_del
        self.dialog_del.open()
    def start_selection_mode(self): self.selection_mode = True; self.selected_ids = []; self.run_filter()
    def exit_selection_mode(self): self.selection_mode = False; self.selected_ids = []; self.run_filter()
    def toggle_selection(self, oid):
        if oid in self.selected_ids: self.selected_ids.remove(oid)
        else: self.selected_ids.append(oid)
        self.run_filter()
    def delete_selected_items(self):
        for oid in self.selected_ids: db.delete_order(oid)
        self.exit_selection_mode()
    def confirm_delete_all(self):
        d2 = MDDialog(title="¿BORRAR TODO?", text="Se borrarán TODOS los pedidos visibles.", buttons=[MDFlatButton(text="NO", on_release=lambda x: d2.dismiss()), MDRaisedButton(text="SÍ", md_bg_color=(1,0,0,1), on_release=lambda x: self.do_clear_all(d2))])
        d2.open()
    def do_clear_all(self, d): 
        # Borra solo lo filtrado
        all_filtered = [] 
        self.run_filter_delete_logic()
        d.dismiss()
        self.run_filter()

    def run_filter_delete_logic(self):
        all_orders = db.get_report_data()
        now = datetime.now()
        for o in all_orders:
            if not o[7]: continue
            d_obj = datetime.strptime(o[7], "%Y-%m-%d %H:%M:%S")
            match = True
            if self.sel_filter == "Hoy":
                if d_obj.date() != now.date(): match = False
            elif self.sel_filter == "Última Semana":
                if d_obj < now - timedelta(days=7): match = False
            elif self.sel_filter == "Último Mes":
                if d_obj < now - timedelta(days=30): match = False
            elif self.sel_filter == "Último Año":
                if d_obj < now - timedelta(days=365): match = False
            elif self.sel_filter == "Ninguno":
                if str(d_obj.year) != self.sel_year: match = False
                if self.sel_month != "Todos" and f"{d_obj.month:02d}" != self.sel_month: match = False
                if self.sel_day != "Todos" and str(d_obj.day) != self.sel_day: match = False
            if match:
                db.delete_order(o[0])

    def show_details_report(self, order):
        details = order[2]
        try:
            cart = json.loads(order[10])
            details = ""
            for item in cart: details += f"[b]{item['qty']}x[/b] {item['desc']} - {item['price']} Bs\n"
            if order[9] > 0: details += f"Moto: {order[9]} Bs"
        except: pass
        content = DetailDialogContent()
        content.title_txt = order[1]; content.date_txt = order[7]; content.details_txt = details; content.total_txt = f"{order[3]} Bs"
        content.ids.action_area.add_widget(MDRaisedButton(text="CERRAR", size_hint_x=0.8, pos_hint={"center_x":0.5}, on_release=lambda x: self.dialog.dismiss()))
        self.dialog = MDDialog(type="custom", content_cls=content); self.dialog.open()

# --- ADD ORDER LOGIC ---
class CartItem(OneLineAvatarIconListItem):
    def __init__(self, item_data, index, remove_callback, **kwargs):
        super().__init__(**kwargs)
        self.text = f"{item_data['qty']}x {item_data['desc']} ({item_data['price']} Bs)"
        icon = IconRightWidget(icon="delete", theme_text_color="Custom", text_color=(1,0,0,1))
        icon.bind(on_release=lambda x: remove_callback(index))
        self.add_widget(icon)

class AddOrderScreen(Screen):
    editing_id = None; cart = []
    sel_food = "Pollo Broaster"; sel_cut = "Pierna"; sel_variant = "Normal (Arroz y Papa)"
    sel_soda = "Ninguna"; sel_delivery = "Para Mesa"; sel_qty_food = "1"; sel_qty_soda = "1"

    def __init__(self, **kwargs): super().__init__(**kwargs); self.menus = {}
    def on_enter(self):
        if not self.menus: self.create_menus()
        self.update_ui_state()
    def create_menus(self):
        foods = ["Pollo Broaster", "Pollo a la Plancha", "Hamburguesa", "Salchipapa", "Solo Porción", "Ninguna"]
        cuts = ["Ala", "Pierna", "Contra", "Pecho"]
        variants = ["Normal (Arroz y Papa)", "Solo Papa", "Solo Arroz", "Ninguna"]
        sodas = ["Ninguna", "Mendocina 3L", "Mendocina 1L", "Coca 3L", "Coca Peque", "Oro Peque"]
        delivery = ["Para Mesa", "Para Llevar (Persona)", "Para Llevar (Moto)"]
        quantities = [str(i) for i in range(1, 21)]
        self.menus['food'] = self._make(foods, self.ids.btn_food, 'sel_food')
        self.menus['cut'] = self._make(cuts, self.ids.btn_cut, 'sel_cut')
        self.menus['variant'] = self._make(variants, self.ids.btn_variant, 'sel_variant')
        self.menus['soda'] = self._make(sodas, self.ids.btn_soda, 'sel_soda')
        self.menus['delivery'] = self._make(delivery, self.ids.btn_delivery, 'sel_delivery')
        self.menus['qty_food'] = self._make(quantities, self.ids.btn_qty_food, 'sel_qty_food')
        self.menus['qty_soda'] = self._make(quantities, self.ids.btn_qty_soda, 'sel_qty_soda')
    def _make(self, items, btn, var):
        # Aumentamos width_mult a 5 para que el menú sea más ancho y quepa texto largo
        return MDDropdownMenu(caller=btn, items=[{"text": i, "viewclass": "OneLineListItem", "on_release": lambda x=i: self.set_item(x, btn, var)} for i in items], width_mult=5, max_height=300)
    def set_item(self, txt, btn, var):
        setattr(self, var, txt); btn.text = txt; btn.text_color = (0,0,0,1)
        k = var.replace('sel_', ''); 
        if k in self.menus: self.menus[k].dismiss()
        if var == "sel_delivery": self.check_moto()
        if var in ["sel_food", "sel_soda"]: self.update_ui_state()

    def check_moto(self):
        if self.sel_delivery == "Para Llevar (Moto)":
            self.ids.moto_input.disabled = False; self.ids.moto_input.opacity = 1
        else:
            self.ids.moto_input.disabled = True; self.ids.moto_input.opacity = 0; self.ids.moto_input.text = ""

    def update_ui_state(self):
        # 1. BLOQUEO DE SODA
        if self.sel_soda != "Ninguna":
            self.disable(self.ids.btn_food); self.disable(self.ids.btn_cut); self.disable(self.ids.btn_variant)
            self.ids.btn_qty_food.disabled = True
        else:
            self.enable(self.ids.btn_food)
            self.ids.btn_qty_food.disabled = False
            f = self.sel_food
            if f == "Ninguna":
                self.disable(self.ids.btn_cut); self.disable(self.ids.btn_variant)
            else:
                # Presa solo Broaster
                if f == "Pollo Broaster": self.enable(self.ids.btn_cut)
                else: self.disable(self.ids.btn_cut)
                
                # Guarnicion (Bloquear en Plancha/Burger/Salchi)
                if f in ["Hamburguesa", "Salchipapa", "Pollo a la Plancha"]: self.disable(self.ids.btn_variant)
                else: self.enable(self.ids.btn_variant)

    def enable(self, btn): btn.disabled=False; btn.md_bg_color=(1,1,1,0); btn.text_color=(0,0,0,1)
    def disable(self, btn): btn.disabled=True; btn.text="---"; btn.md_bg_color=(0.9,0.9,0.9,1); btn.text_color=(0.5,0.5,0.5,1)
    def open_menu(self, k): self.menus[k].open()
    def open_qty_menu(self, k): self.menus[f'qty_{k}'].open()

    def get_prices(self):
        f = self.sel_food; fp = 0; fd = ""
        # Si Soda está activa, ignoramos comida
        if self.sel_soda == "Ninguna" and f != "Ninguna":
            if f == "Pollo Broaster":
                b = 18 if self.sel_cut == "Pecho" else 16
                if self.sel_variant == "Solo Papa": b+=1
                fp=b; fd=f"Pollo {self.sel_cut}"
                if self.sel_variant != "Normal (Arroz y Papa)": fd+=f" [{self.sel_variant}]"
            elif f == "Pollo a la Plancha": fp=20; fd="Pollo Plancha"
            elif f == "Hamburguesa": fp=17; fd="Hamburguesa"
            elif f == "Salchipapa": fp=16; fd="Salchipapa"
            elif f == "Solo Porción":
                p=4
                if self.sel_variant=="Normal (Arroz y Papa)": p=8
                elif self.sel_variant=="Solo Papa": p=7
                fp=p; fd=f"Porción {self.sel_variant}"
        
        s = self.sel_soda; sp=0; sd=""
        sods = {"Mendocina 3L": 15, "Mendocina 1L": 7, "Coca 3L": 20, "Coca Peque": 5, "Oro Peque": 3}
        if s in sods: sp=sods[s]; sd=s
        return fp, fd, sp, sd

    def add_item_to_cart(self):
        fp, fd, sp, sd = self.get_prices()
        if fp > 0:
            q = int(self.sel_qty_food)
            self.cart.append({"qty": q, "desc": fd, "unit_price": fp, "price": fp*q})
        if sp > 0:
            q = int(self.sel_qty_soda)
            self.cart.append({"qty": q, "desc": sd, "unit_price": sp, "price": sp*q})
        
        self.update_cart()
        # Reset visual
        self.set_item("1", self.ids.btn_qty_food, "sel_qty_food")
        self.set_item("1", self.ids.btn_qty_soda, "sel_qty_soda")
        self.set_item("Ninguna", self.ids.btn_soda, "sel_soda")

    def remove_item(self, i):
        if 0 <= i < len(self.cart): self.cart.pop(i); self.update_cart()
    def update_cart(self):
        self.ids.cart_list.clear_widgets(); gt = 0
        for i, item in enumerate(self.cart):
            gt += item['price']; self.ids.cart_list.add_widget(CartItem(item, i, self.remove_item))
        try: gt += float(self.ids.moto_input.text)
        except: pass
        self.ids.lbl_total.text = f"TOTAL: {gt} Bs"
    def save_order_final(self):
        if not self.cart: return
        name = self.ids.name_input.text or "Cliente"
        total = 0; details = ""
        for i in self.cart: total+=i['price']; details+=f"{i['qty']}x {i['desc']} ({i['price']} Bs)\n"
        moto=0
        try: moto=float(self.ids.moto_input.text); total+=moto; details+=f"Moto: {moto} Bs\n"
        except: pass
        details+=f"({self.sel_delivery})"
        if self.editing_id: db.update_order(self.editing_id, name, details, total, self.sel_delivery, moto, self.cart)
        else: db.add_order(name, details, total, self.sel_delivery, moto, self.cart)
        app = MDApp.get_running_app(); app.refresh_home(); app.cancel_add()
    def clear_form(self):
        self.editing_id = None; self.cart = []; self.update_cart()
        self.ids.toolbar.title = "Nuevo Pedido"; self.ids.save_btn.text = "GUARDAR PEDIDO"
        self.ids.name_input.text = ""; self.ids.moto_input.text = ""
        self.set_item("Pollo Broaster", self.ids.btn_food, "sel_food")
        self.set_item("Pierna", self.ids.btn_cut, "sel_cut")
        self.set_item("Normal (Arroz y Papa)", self.ids.btn_variant, "sel_variant")
        self.set_item("Ninguna", self.ids.btn_soda, "sel_soda")
        self.set_item("Para Mesa", self.ids.btn_delivery, "sel_delivery")
        self.set_item("1", self.ids.btn_qty_food, "sel_qty_food")
        self.set_item("1", self.ids.btn_qty_soda, "sel_qty_soda")
    def load_order_data(self, order_data):
        self.editing_id = order_data[0]; self.ids.toolbar.title = "Editar Pedido"; self.ids.save_btn.text = "ACTUALIZAR"
        self.ids.name_input.text = order_data[1]; self.set_item(order_data[8], self.ids.btn_delivery, "sel_delivery")
        if order_data[9]: self.ids.moto_input.text = str(order_data[9])
        try: 
            if order_data[10]: self.cart = json.loads(order_data[10]); self.update_cart()
        except: pass

class HomeScreen(Screen): pass

class PollosApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Orange"
        Builder.load_string(KV)
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(AddOrderScreen(name='add_order'))
        sm.add_widget(HistoryMenuScreen(name='history_menu'))
        sm.add_widget(OrderListScreen(name='order_list'))
        sm.add_widget(ReportScreen(name='report'))
        return sm
    def on_start(self): self.refresh_home()
    def go_to_add(self):
        s = self.root.get_screen('add_order'); s.clear_form()
        self.root.transition.direction = 'left'; self.root.current = 'add_order'
    def edit_order(self, oid):
        d = db.get_order_by_id(oid)
        if d:
            s = self.root.get_screen('add_order'); s.load_order_data(d)
            self.root.transition.direction = 'left'; self.root.current = 'add_order'
    def delete_order(self, oid): db.delete_order(oid); self.refresh_home()
    
    # HISTORY NAVIGATION
    def go_to_history_menu(self): self.root.transition.direction = 'left'; self.root.current = 'history_menu'
    def go_to_delivered(self):
        s = self.root.get_screen('order_list'); s.mode = "delivered"; s.load_data()
        self.root.transition.direction = 'left'; self.root.current = 'order_list'
    def go_to_credit(self):
        s = self.root.get_screen('order_list'); s.mode = "credit"; s.load_data()
        self.root.transition.direction = 'left'; self.root.current = 'order_list'
    def go_to_report(self): self.root.transition.direction = 'left'; self.root.current = 'report'
    
    def confirm_clear_history(self):
        if self.root.current == 'order_list':
            self.root.get_screen('order_list').ask_delete_mode()

    def go_home(self): self.root.transition.direction = 'right'; self.root.current = 'home'
    def cancel_add(self): self.root.transition.direction = 'right'; self.root.current = 'home'
    def refresh_home(self):
        home = self.root.get_screen('home'); grid = home.ids.orders_grid; grid.clear_widgets()
        orders = db.get_active_orders()
        for o in orders:
            c = OrderCard(); c.order_id=o[0]; c.customer_name=o[1]; c.order_details=o[2]; c.total_price=o[3]
            grid.add_widget(c)

if __name__ == '__main__':
    PollosApp().run()