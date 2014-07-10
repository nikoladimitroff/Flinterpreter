import itertools
import re
import sys

from parsley import makeGrammar


class Operator:
    Constant = "CONST"
    PrimitiveFunction = "PRIMITIVE"
    Bool = "BOOL"
    IfThenElse = "IFELSE"
    Function = r"FUNCTION"

    class Primitive:
        Plus = "+"
        Sub = "-"
        Mul = "*"
        Div = "/"
        Modulo = "%"

    class Comparer:
        LT = "<"
        GT = ">"
        EQ = "=="
        LET = "<="
        GET = ">="

    class BoolOp:
        NOT = "not"
        AND = "and"
        OR = "or"


class Flinterpreter:
    WHERE = "where"
    GRAMMAR = """
        ws = ' '*
        ws1 = ' '+
        term = term:t1 ws nat_op:op ws term:t2 -> ('PRIMITIVE', op, t1, t2)
               |'(' ws term:t0 ws ')' -> t0
               | 'if ' bool:cond ' then ' term:t1 ' else ' term:t2 -> ('IFELSE', cond, t1, t2)
               | fname:f '(' fargs:arguments ')' -> ('FUNCTION', f, arguments)
               | const:n -> n
        const = <'-'? digit+>:n -> ("CONST", int(n))
        bool = bool:b1 ws1 bool_op:op ws1 bool:b2 -> ('BOOL', op, b1, b2)
               | term:t1 ws comparer:comp ws term:t2 -> ('BOOL', comp, t1, t2)
               | 'not' ws1 bool:b -> ('BOOL', 'not', b)
        bool_op = 'and' | 'or'
        comparer = '<' | '<=' | '>' | '>=' | '==' | '!='
        nat_op =  '*' | '/' | '+' | '-' | '%'
    """

    ARGS_BY_VALUE = """
        fargs = term:head ',' ws fargs:tail -> [head] + tail
               | term:arg -> [arg]
        """

    ARGS_BY_NAME = """
        fargs = <term>:head ',' ws fargs:tail -> [head] + tail
               | <term>:arg -> [arg]
        """

    def __init__(self, code, by_name=False, verbose=False):
        lines = [line.strip() for line in code.strip().split("\n")]
        self.head = lines[0].replace(Flinterpreter.WHERE, "").strip()
        body = lines[1:]
        self.functions = {function[0]: function[1:]
                          for function in map(self.__extract_function, body)}

        grammar_def = Flinterpreter.GRAMMAR
        function_eval = None
        if by_name:
            grammar_def += Flinterpreter.ARGS_BY_NAME
            function_eval = self.__evaluate_function_name
        else:
            grammar_def += Flinterpreter.ARGS_BY_VALUE
            function_eval = self.__evaluate_function_value

        fnames = " | ".join("'{}'".format(name) for name in self.functions.keys())
        if len(fnames) == 0:
            fnames = "'THERE ARE NO EXTRA FUNCTIONS'"
        grammar_def += "fname = " + fnames

        self.grammar = makeGrammar(grammar_def, {})

        self.verbose = verbose

        self.eval_functions = {
            Operator.Constant: lambda x: x[0],
            Operator.PrimitiveFunction: self.__evaluate_primitive,
            Operator.IfThenElse: self.__evaluate_ifelse,
            Operator.Function: function_eval,
            Operator.Bool: self.__evaluate_bool,
        }

    def __extract_function(self, line):
        name = line[:line.index('(')].strip()
        args = line[line.index('(') + 1: line.index(')')] \
               .replace(" ", "").split(",")
        body = line[line.index('=') + 2:].strip()

        return (name, args, body)

    def evaluate(self):
        try:
            return self.__evaluate_expression(self.head)
        except Exception as e:
            print "An error occurred: ", e
            return -1

    def __evaluate_primitive(self, primitive):
        operator = primitive[0]
        operands = primitive[1:]

        left = self.__evaluate_expression(operands[0])
        right = self.__evaluate_expression(operands[1])
        return eval("left {0} right".format(operator))

    def __evaluate_ifelse(self, ifelse_expr):
        boolean = ifelse_expr[0]
        if self.__evaluate_bool(boolean):
            return self.__evaluate_expression(ifelse_expr[1])
        return self.__evaluate_expression(ifelse_expr[2])

    def __evaluate_function_value(self, func_call):
        fname, args = func_call

        arg_values = [self.__evaluate_expression(arg) for arg in args]
        return self.__evaluate_function_name((fname, arg_values))

    def __evaluate_function_name(self, func_call):
        fname, args = func_call

        formal_args, function_body = self.functions[fname]
        for i in range(len(formal_args)):
            pattern = r"\b{0}\b".format(formal_args[i])
            function_body = re.sub(pattern, str(args[i]), function_body)

        if self.verbose:
            print "EVALUATING: ", function_body
        return self.__evaluate_expression(function_body)

    def __evaluate_bool(self, bool_expr):
        bool_expr = bool_expr[1:]
        operator = bool_expr[0]
        if operator is Operator.BoolOp.NOT:
            return not self.__evaluate_bool(bool_expr[1])

        left = None
        right = None
        if operator in Operator.BoolOp.__dict__.values():
            left = self.__evaluate_bool(bool_expr[1])
            right = self.__evaluate_bool(bool_expr[2])
        if operator in Operator.Comparer.__dict__.values():
            left = self.__evaluate_expression(bool_expr[1])
            right = self.__evaluate_expression(bool_expr[2])

        return eval("left {0} right".format(operator))

    def __evaluate_expression(self, expression):
        if isinstance(expression, str):
            expr_tree = self.grammar(expression).term()
        else:
            expr_tree = expression

        return self.eval_functions[expr_tree[0]](expr_tree[1:])


def main():
    x_squared = """
        h(10) where
        h(x) = f(x, x)
        f(x, y) = if y == 0 then 0 else g(x, f(x, y - 1))
        g(x, y) = if x == 0 then y else g(x - 1, y) + 1
    """
    
    power = """
        power(5, 3) where
        power(x, y) = if y == 0 then 1 else mul(x, power(x, y - 1))
        mul(x, y) = if y == 0 then 0 else mul(x, y - 1) + x
    """

    factoriel = """
        f(10) where
        f(x) = h(x, 1)
        h(x, y) = if x == 1 then 1 else h(x - 1, x * y)
    """

    fibonacci = """
        fib(6) where
        fib(x) = if x == 0 then 1 else if x == 1 then 1 else fib(x - 1) + fib(x - 2)
    """

    soskov = """
        mul(0, 5 / 0)) where
        mul(x, y) = if x == 0 then 0 else mul(x - 1, y) + x
        div(x, y) = x / y
    """

    integer_div = """
        f(5, 5) where
        f(x, y) = if x % 3 == 0 then x / 3 else f((x - 1), f((2*x) - 2, y))
    """

    # Double maximum call stack since we really need a deep call stack
    sys.setrecursionlimit(sys.getrecursionlimit() * 2)

    code = power    
    by_name = False
    verbose = False

    parser = Flinterpreter(code, by_name=by_name, verbose=verbose)
    result = parser.evaluate()
    print "Result: ", result


main()
