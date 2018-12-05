from itertools import izip

class Engine(object):
    def execute(self, node, exec_cache=None):
        if exec_cache is None:
            exec_cache = {}
        result = node.execute(exec_cache)
        for a, val in izip(node.out_attrs, result):
            exec_cache[a] = val

        return result


engine = Engine()


class NodeAttribute(object):
    def __init__(self, name, parent=None, source_attr=None):
        self.name = name
        self.parent = parent
        self.source_attr = source_attr

    def obtain_value(self, exec_cache):
        if self.parent is not None:
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
    def __init__(self, name, in_attrs, out_attrs):
        self.name = name
        self.in_attrs = in_attrs
        self.out_attrs = out_attrs


class Add(Node):
    def __init__(self):
        super(Add, self).__init__("Add", [NodeAttribute("a"), NodeAttribute(
            "b")], [NodeAttribute("result", self)])

    def execute(self, exec_cache):
        return self.in_attrs[0].get(exec_cache) + self.in_attrs[1].get(exec_cache),


class Substract(Node):
    def __init__(self):
        super(Substract, self).__init__("Add", [NodeAttribute("a"), NodeAttribute(
            "b")], [NodeAttribute("result", self)])

    def execute(self, exec_cache):
        return self.in_attrs[0].get(exec_cache) - self.in_attrs[1].get(exec_cache),

class Multiply(Node):
    def __init__(self):
        super(Multiply, self).__init__("Add", [NodeAttribute("a"), NodeAttribute(
            "b")], [NodeAttribute("result", self)])

    def execute(self, exec_cache):
        return self.in_attrs[0].get(exec_cache) * self.in_attrs[1].get(exec_cache),

class Divide(Node):
    def __init__(self):
        super(Divide, self).__init__("Add", [NodeAttribute("a"), NodeAttribute(
            "b")], [NodeAttribute("result", self)])

    def execute(self, exec_cache):
        return self.in_attrs[0].get(exec_cache) / self.in_attrs[1].get(exec_cache),


add1 = Add()
add2 = Add()
add3 = Add()
substract1 = Substract()
multiply1 = Multiply()
divide1 = Divide()

add3.in_attrs[0].source_attr = add1.out_attrs[0]
add3.in_attrs[1].source_attr = add2.out_attrs[0]
substract1.in_attrs[0].source_attr = add3.out_attrs[0]
substract1.in_attrs[1].source_attr = ConstAttribute(5)
multiply1.in_attrs[0].source_attr = substract1.out_attrs[0]
multiply1.in_attrs[1].source_attr = ConstAttribute(3)
divide1.in_attrs[0].source_attr = multiply1.out_attrs[0]
divide1.in_attrs[1].source_attr = ConstAttribute(5)

exec_cache = {
    add1.in_attrs[0]: 1,
    add1.in_attrs[1]: 2,
    add2.in_attrs[0]: 3,
    add2.in_attrs[1]: 4,
}

print engine.execute(divide1, exec_cache)
