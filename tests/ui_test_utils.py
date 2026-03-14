from unittest.mock import MagicMock


class MockBase(object):
    def __init__(self, master=None, *args, **kwargs):
        self.master = master
        self._config = {}
        self.destroy = MagicMock()
        self.pack = MagicMock()
        self.pack_forget = MagicMock()
        self.place = MagicMock()
        self.place_forget = MagicMock()
        self.grid = MagicMock()
        self.grid_forget = MagicMock()
        self.configure = MagicMock(side_effect=self._mock_configure)
        self.cget = MagicMock(side_effect=self._mock_cget)
        self.get = MagicMock(return_value="")
        self.set = MagicMock()
        self.insert = MagicMock()
        self.delete = MagicMock()
        self.after = MagicMock(side_effect=self._mock_after)
        self.after_main = MagicMock(side_effect=self._mock_after)
        self.winfo_children = MagicMock(return_value=[])
        self.winfo_toplevel = MagicMock(return_value=self)
        self.lift = MagicMock()
        self.focus_force = MagicMock()
        # select/deselect should be mocked only if they don't exist
        if not hasattr(self, "select"):
            self.select = MagicMock()
        if not hasattr(self, "deselect"):
            self.deselect = MagicMock()

        for k, v in kwargs.items():
            setattr(self, k, v)
            self._config[k] = v

    def _mock_configure(self, **kwargs):
        self._config.update(kwargs)
        for k, v in kwargs.items():
            setattr(self, k, v)

    def _mock_cget(self, attr):
        return self._config.get(attr, "")

    def _mock_after(self, ms, func=None, *args):
        if func and callable(func):
            func()

    def grid_columnconfigure(self, *args, **kwargs):
        pass

    def grid_rowconfigure(self, *args, **kwargs):
        pass

    def pack_propagate(self, *args):
        pass

    def grid_propagate(self, *args):
        pass

    def bind(self, *args, **kwargs):
        pass

    def unbind(self, *args, **kwargs):
        pass

    def winfo_rootx(self):
        return 0

    def winfo_rooty(self):
        return 0

    def winfo_height(self):
        return 100

    def winfo_width(self):
        return 100

    def winfo_x(self):
        return 0

    def winfo_y(self):
        return 0

    def update_idletasks(self):
        pass

    def update(self):
        pass

    def see(self, *args, **kwargs):
        pass

    def add(self, *args, **kwargs):
        return self

    def tab(self, *args, **kwargs):
        return self

    def create_rectangle(self, *args, **kwargs):
        return 1

    def create_text(self, *args, **kwargs):
        return 1

    def itemconfig(self, *args, **kwargs):
        pass

    def coords(self, *args, **kwargs):
        pass

    def delete(self, *args, **kwargs):
        pass


class MockCTk(MockBase):
    def title(self, *args):
        pass

    def geometry(self, *args):
        pass

    def withdraw(self):
        pass

    def deiconify(self):
        pass

    def mainloop(self):
        pass

    def quit(self):
        pass

    def resizable(self, *args):
        pass


class MockCTkToplevel(MockCTk):
    def __init__(self, master=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master

    def transient(self, *args):
        pass

    def grab_set(self):
        pass

    def lift(self):
        pass

    def focus_force(self):
        pass


class MockDnDWrapper(object):
    def drop_target_register(self, *args):
        pass

    def dnd_bind(self, *args):
        pass


class MockModule(object):
    pass


class MockVar(object):
    def __init__(self, master=None, value=None, name=None):
        self._value = value

    def get(self):
        return self._value

    def set(self, value):
        self._value = value


def get_ui_mocks():
    mock_ctk = MockModule()
    mock_ctk.CTk = MockCTk
    mock_ctk.CTkFrame = MockBase
    mock_ctk.CTkScrollableFrame = MockBase
    mock_ctk.CTkToplevel = MockCTkToplevel
    mock_ctk.CTkLabel = MagicMock(side_effect=lambda *args, **kwargs: MockBase(*args, **kwargs))
    mock_ctk.CTkButton = MagicMock(side_effect=lambda *args, **kwargs: MockBase(*args, **kwargs))
    mock_ctk.CTkSwitch = MagicMock(side_effect=lambda *args, **kwargs: MockBase(*args, **kwargs))
    mock_ctk.CTkOptionMenu = MagicMock(side_effect=lambda *args, **kwargs: MockBase(*args, **kwargs))
    mock_ctk.CTkCheckBox = MagicMock(side_effect=lambda *args, **kwargs: MockBase(*args, **kwargs))
    mock_ctk.CTkSlider = MagicMock(side_effect=lambda *args, **kwargs: MockBase(*args, **kwargs))
    mock_ctk.CTkProgressBar = MagicMock(side_effect=lambda *args, **kwargs: MockBase(*args, **kwargs))
    mock_ctk.CTkCanvas = MagicMock(side_effect=lambda *args, **kwargs: MockBase(*args, **kwargs))
    mock_ctk.CTkTextbox = MockBase
    mock_ctk.CTkTabview = MagicMock(side_effect=lambda *args, **kwargs: MockBase(*args, **kwargs))
    mock_ctk.BooleanVar = MockVar
    mock_ctk.StringVar = MockVar
    mock_ctk.set_appearance_mode = MagicMock()
    mock_ctk.get_appearance_mode = MagicMock(return_value="Light")
    mock_ctk.set_default_color_theme = MagicMock()
    mock_ctk.CTkFont = MagicMock()
    mock_ctk.CTkInputDialog = MagicMock()

    mock_dnd = MockModule()
    mock_dnd.TkinterDnD = MagicMock()
    mock_dnd.DnDWrapper = MockDnDWrapper
    mock_dnd.DND_FILES = "DND_FILES"

    return mock_ctk, mock_dnd
