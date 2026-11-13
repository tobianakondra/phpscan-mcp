<?php

// Sample legacy PHP application with classic vulnerabilities
// This file is used by tests/sample_vulnerable_app to validate
// the audit server. It is read-only: the audit tools must not
// modify or delete any of the files below.

// 1. SQL injection via $_GET (mysql_query, legacy PHP)
if (isset($_GET['id'])) {
    $id = $_GET['id'];
    $sql = "SELECT * FROM users WHERE id = $id";
    $result = mysql_query($sql);
}

// 2. Unsecure file inclusion via $_GET
if (isset($_GET['page'])) {
    $page = $_GET['page'];
    include($page . '.php');
}

// 3. Deprecated / risky function calls
$data = $_POST['data'];
$obj = unserialize($data);

echo "Legacy PHP sample app loaded.";
