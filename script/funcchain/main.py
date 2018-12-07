from itertools import izip
import itertools
from collections import OrderedDict
from enum import Enum


class Engine(object):
    def execute(self, node, exec_cache=None):
        if exec_cache is None:
            exec_cache = {}
        while node is not None:
            result = node.obtain_values_and_execute(exec_cache)
            if result is not None:
                for a, val in izip(node.out_attrs.itervalues(), result):
                    exec_cache[a] = val

            node = node.next_node

        return exec_cache


engine = Engine()


class NodeType:
    In = 0
    Out = 1


class NodeAttribute(object):
    def __init__(self, name, node_type, parent=None, source_attr=None):
        self.name = name
        self.node_type = node_type
        self.parent = parent
        self.source_attr = source_attr

    def obtain_value(self, exec_cache):
        if self.node_type == NodeType.Out and self.parent is not None:
            engine.execute(self.parent, exec_cache)
            return self.get(exec_cache)
        if self.source_attr is not None:
            return self.source_attr.get(exec_cache)
        raise

    def get(self, exec_cache):
        if self in exec_cache:
            return exec_cache[self]
        return self.obtain_value(exec_cache)


class ConstAttribute(object):
    def __init__(self, value):
        self.value = value

    def get(self, exec_cache):
        return self.value


class Node(object):
    def __init__(self, name=None):
        if name is None:
            self.name = self.__class__.__name__
        else:
            self.name = name
        self.attrs = OrderedDict()
        self.next_node = None

    def __getattr__(self, name):
        return self.attrs[name]

    def obtain_values_and_execute(self, exec_cache):
        return self.execute(exec_cache=exec_cache, **{
            name: attr.get(exec_cache)
            for name, attr in self.in_attrs.iteritems()
        })

    @property
    def in_attrs(self):
        return OrderedDict([(name, val) for name, val in self.attrs.iteritems() if val.node_type == NodeType.In])

    @property
    def out_attrs(self):
        return OrderedDict([(name, val) for name, val in self.attrs.iteritems() if val.node_type == NodeType.Out])


class _CountedObject(object):
    counter = itertools.count()

    def __init__(self):
        self.counter = _CountedObject.counter.next()


class InAttrKls(_CountedObject):
    node_type = NodeType.In

    def __init__(self, const=None):
        self.const = const


class OutAttrKls(_CountedObject):
    node_type = NodeType.Out


def class_wrapper(cls):
    attrs = sorted([(name, attr)
                    for name, attr in cls.__dict__.items()
                    if isinstance(attr, (InAttrKls, OutAttrKls))], key=lambda x: x[1].counter)
    for name, _ in attrs:
        delattr(cls, name)

    def init(self):
        super(cls, self).__init__()
        self.attrs.update([(name, NodeAttribute(name, attr.node_type, self,
                                                None if attr.node_type != NodeType.In or attr.const is None else ConstAttribute(attr.const))) for name, attr in attrs])

    cls.__init__ = init
    return cls


@class_wrapper
class BinaryOperator(Node):
    a = chain.In()
    b = InAttrKls()
    result = OutAttrKls()


class Add(BinaryOperator):
    def execute(self, a, b, exec_cache):
        return a + b,


class Substract(BinaryOperator):
    def execute(self, a, b, exec_cache):
        return a - b,


class Multiply(BinaryOperator):
    def execute(self, a, b, exec_cache):
        return a * b,

class Divide(BinaryOperator):
    def execute(self, a, b, exec_cache):
        return a / b,

@class_wrapper
class GetQ(Node):
    inv_container = InAttrKls()
    item_id = InAttrKls()
    inv_id = InAttrKls()
    quantity = OutAttrKls()

    def execute(self, inv_container, item_id, inv_id, exec_cache):
        return inv[inv_id][item_id],


@class_wrapper
class FilterInvClass(Node):
    func = InAttrKls()
    inv_class = InAttrKls()
    inv = InAttrKls()
    inv_id = InAttrKls()

    def execute(self, func, inv_class, inv, inv_id, exec_cache):
        if inv_id.starts_with(inv_class):
            engine.execute(func, exec_cache)


@class_wrapper
class FilterOneTime(Node):
    func = InAttrKls()
    inv = InAttrKls()

    def execute(self, func, inv, exec_cache):
        if inv.get("rules", {}).get("Rule1", 0) == 0:
            engine.execute(func, exec_cache)


@class_wrapper
class GiveItems(Node):
    inv = InAttrKls()
    inv_id = InAttrKls()
    item_set = InAttrKls()
    multiplier = InAttrKls()
    modifications = OutAttrKls()

    def execute(self, inv, inv_id, item_set, multiplier, exec_cache):
        result = {inv_id: {item_id: q * multiplier for item_id,
                           q in item_set.iteritems()}}
        return result,


@class_wrapper
class MergeResult(Node):
    struct = InAttrKls()
    to_merge = InAttrKls()

    def execute(self, struct, to_merge, exec_cache):
        struct.update(to_merge)


@class_wrapper
class Print(Node):
    val = InAttrKls()

    def execute(self, val, exec_cache):
        print val


@class_wrapper
class ForEachInv(Node):
    inv_container = InAttrKls()
    func = InAttrKls()
    completed = InAttrKls()
    inv_id = OutAttrKls()
    inv_element = OutAttrKls()

    def execute(self, inv_container, func, completed, exec_cache):
        inv_container = self.inv_container.get(exec_cache)
        for inv_id, inv in inv_container.iteritems():
            exec_cache[self.inv_id] = inv_id
            exec_cache[self.inv_element] = inv
            engine.execute(self.func.get(exec_cache), exec_cache)

        engine.execute(self.completed.get(exec_cache), exec_cache)


getQ = GetQ()
for_each = ForEachInv()
filt = FilterOneTime()
give = GiveItems()
merge = MergeResult()
print_node = Print()

# DATA
inv = {
    "Global-0": {
        "a": 1,
        "b": 1,
        "c": 2,
    },
    "Save-0": {
        "q": 1,
        "w": 2,
        "e": 3,
        "rules": {
            "Rule1": 1
        }
    },
    "Save-1": {
        "q": 1,
        "w": 2,
        "e": 3,
    },
    "Save-2": {
        "q": 1,
        "w": 2,
        "e": 3,
    },
}
item_set = {
    "ADDED1": 1,
    "ADDED2": 2
}
class_to_add = "Save"
inv_id_for_q = "Global-0"


# Connection binding
for_each.func.source_attr = ConstAttribute(filt)
for_each.completed.source_attr = ConstAttribute(print_node)
filt.func.source_attr = ConstAttribute(give)
filt.inv.source_attr = for_each.inv_element
give.inv.source_attr = for_each.inv_element
give.inv_id.source_attr = for_each.inv_id
give.next_node = merge
result = ConstAttribute({})
merge.struct.source_attr = result
merge.to_merge.source_attr = give.modifications
print_node.val.source_attr = result


exec_cache = {
    for_each.inv_container: inv,
    give.item_set: item_set,
    give.multiplier: 1,
}

print engine.execute(for_each, exec_cache)
print result.get(None)
