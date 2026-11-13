<?php

// Sample file exercising deprecated / risky PHP APIs.
// It exercises mysql_connect, eval and create_function.

// mysql_connect is removed in PHP 7+
$conn = mysql_connect('localhost', 'user', 'pass', true);

// eval() / create_function are discouraged
$z = 'world';
$code = create_function('$x', 'return $x . " " . ' . var_export($z, true) . ';');
echo $code('hello');

// Another eval example
$pattern = '/^foo/';
eval('$result = preg_match($pattern, $input);');
