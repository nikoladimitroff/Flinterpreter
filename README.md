# Flinterpreter
## An interpreter for a function language, hooray!
- - -
Flinterpreter is a small program written in python 2.7 (~170 loc). The only file worth looking is `interpreter.py`, the others constitute the awesome library [`parsley`](parsley).
The interepter runs programs written in a special LISP-like language (taught in the course Programming language semantics @ [FMI, SU](fmi))
that I'll call FL for short.

First, let us see some examples of programs written in FL.
## Examples
*Factoriel:*
```
factoriel(10) where
factoriel(x) = if x == 0 then 1 else x * factoriel(x - 1)

```

*Power:*
```
power(5,3) where
power(x, y) = if y == 0 then 1 else mul(x, power(x, y - 1)
mul(x, y) = if y == 0 then 0 else mul(x, y - 1) + x 
```

To run the programs above, pass their code as string to the constructor of `Flinterpreter`:

```
    interpreter = Flinterpreter(code)
    result = interpreter.evaluate()
    print result
``` 

## Language grammar
As you just saw, FL is extremely simple. Every program consists of a head (the first line) and a list
of functions (each defined on the lines after the first). Empty lines and multiline expressions are not allowed.
The head of the program is any expression followed by the keyword 'where'. 

Currently, there's only a single data type - integers (unlimited in size). 
Supported operations are \+, \-, \*, /, % and they do what you expect them to do.
Other than that, you can also use `if condition then expression else expression` just like you would in Haskell for instance. The `condition` is any boolean expression (e.g. `5 < 4` or `x == y and not y >= 8`). The else is mandatory. 

If anyone cares, here's the FL's grammar:

expression = expression nat\_op expression 
             | if bool then expression1 else expression2
             | function(expression, ..., expression)
             | integer
nat\_op = \+ | \- | \* | / | %
bool = expression comparer expression 
       | bool bool_op bool
       | not bool
comparer = < | <= | >= | > | == | !=
bool\_op = and | or
function = f | g | ... (whatever functions you've declared)


## By value vs by name
A crucial feature of the interpreter is that it supports both call-by-value and call-by-name semantics. Consider the following example:

```
    mul(0, 5 / 0)) where
    mul(x, y) = if x == 0 then 0 else mul(x - 1, y) + x
```
The call-by-value semantic evaluates the arguments to function BEFORE calling the function. In other words, before calling mult in the program above, we must first evaluate `5 / 0`. Since you can divide by zero, this throws an exception and the program halts.

On the other hand, call-by-name defers evaluation as long as possible (it is a form of lazy evaluation). Running the above program will not throw an exception, rather the interpretere substitues `5 / 0` as the formal parameter `y` and then evaluates the expression:

```
    if 0 == 0 then 0 else mul(0 - 1, 5 / 0) + 0
``` 
The condition is true, so we get 0 instead of an error.

You can control which semantics the interpreter is using with the named parameter `by_name`.

In addition, if you'd like to see exactly how the evaluation is running, set the named parameter `verbose` to true.

## Other notes
* Arithmetic operations are not prioritized correctly - `4 * 5 + 3` is equal to `4 * (5 + 3)` as opposed to `(4 * 5) + 3`. This is intentional since it speeds up the interpreter and in most cases you don't rely on operator precedence. Use parenthesis to explicitly denote prioritized operations.



[fmi]: http://fmi.uni-sofia.bg
[parsley]: https://pypi.python.org/pypi/Parsley
