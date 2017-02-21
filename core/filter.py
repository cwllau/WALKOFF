import importlib
from xml.etree import cElementTree as et

from core import arguments
from core.case import callbacks
from core.executionelement import ExecutionElement


class Filter(ExecutionElement):
    def __init__(self, xml=None, parent_name="", action="", args=None, ancestry=None):
        if xml:
            self._from_xml(xml, parent_name, ancestry)
        else:
            ExecutionElement.__init__(self, name=action, parent_name=parent_name, ancestry=ancestry)
            self.action = action
            args = args if args is not None else {}
            self.args = {arg: arguments.Argument(key=arg, value=args[arg], format=type(args[arg]).__name__)
                         for arg in args}
        super(Filter, self)._register_event_callbacks({'FilterSuccess': callbacks.add_flag_entry('Filter success'),
                                                       'FilterError': callbacks.add_flag_entry('Filter error')})

    def _from_xml(self, xml_element, parent_name=None, ancestry=None):
        self.action = xml_element.get('action')
        ExecutionElement.__init__(self, name=self.action, parent_name=parent_name, ancestry=ancestry)
        args = {arg.tag: arguments.Argument(key=arg.tag, value=arg.text, format=arg.get("format")) for arg in
                xml_element.findall("args/*")}
        self.args = {arg: arguments.Argument(key=arg, value=args[arg], format=type(args[arg]).__name__)
                     for arg in args}

    def to_xml(self):
        elem = et.Element("filter")
        elem.set("action", self.action)
        argsElement = et.SubElement(elem, "args")
        for arg in self.args:
            argsElement.append(self.args[arg].to_xml())

        return elem

    def __call__(self, output=None):
        module = self.checkImport()
        if module:
            try:
                result = getattr(module, "main")(args=self.args, value=output)
                self.event_handler.execute_event_code(self, 'FilterSuccess')
                return result
            except Exception:
                self.event_handler.execute_event_code(self, 'FilterError')
                print("FILTER ERROR")
        return output

    def checkImport(self):
        try:
            filterModule = importlib.import_module("core.filters." + self.action)
        except ImportError as e:
            filterModule = None
        finally:
            return filterModule

    def __repr__(self):
        output = {'action': self.action,
                  'args': {arg: self.args[arg].__dict__ for arg in self.args}}
        return str(output)

    def as_json(self):
        return {"action": self.action,
                "args": {arg: self.args[arg].as_json() for arg in self.args}}