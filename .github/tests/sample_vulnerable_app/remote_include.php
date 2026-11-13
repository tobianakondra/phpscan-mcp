<?php

// Sample file exercising remote file inclusion / include of user input.
// It uses include/require with a variable that comes from the user.

if (isset($_GET['file'])) {
    $file = $_GET['file'];
    include($file);          // remote/local include (LFI/RFI risk)
}

if (isset($_GET['inc'])) {
    $inc = $_GET['inc'];
    require_once($inc . '.tpl'); // variable include
}
