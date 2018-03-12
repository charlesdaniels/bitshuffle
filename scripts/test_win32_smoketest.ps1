# test BitShuffle on Windows platforms (for use in AppVeyor)

Write-Output "Performing win32 smoketest... ";
$failed_tests = 0;

$project_tld = Split-Path $PSScriptRoot -Parent
$bitshuffle_bin = Join-Path $project_tld "wrapper.py"
Write-Output "script root is: $PSScriptRoot"
Write-Output "project TLD is: $project_tld"
Write-Output "BitShuffle script is: $bitshuffle_bin"

Write-Output "Testing that BitShuffle can launch without error..."

& $bitshuffle_bin --version
$exitcode = $?;

if ($exitcode) {
    Write-Output "Test succeeded."
} else {
    Write-Warning "Test failed."
    $failed_tests = $failed_tests + 1;
}

# generate a random test file
Get-Process | Out-File "rand_test_file.bin"

$rand_file_hash = (Get-FileHash -Algorithm SHA1 -Path "rand_test_file.bin").Hash

Write-Output "Testing non-pipelined encode/decode..."
& Get-Content "rand_test_file.bin" | $bitshuffle_bin --encode > "test_1.txt" | ForEach-Object {Write-Output "`toutput: $_";}
$ret1 = $?;
& Get-Content "test_1.txt" | $bitshuffle_bin --decode > "test_1.bin" | ForEach-Object {Write-Output "`toutput: $_";}
$ret2 = $?;
$test_hash_1 = (Get-FileHash -Algorithm SHA1 -Path "test_1.bin").Hash
$compare_result = ($rand_file_hash -eq $test_hash_1)

if ($ret1 -and $ret2 -and $compare_result) {
    Write-Output "Test succeeded."
} else {
    Write-Warning "Test failed."
    Write-Output "$rand_file_hash did not match $test_hash_1"
    $failed_tests = $failed_tests + 1;
}


Write-Output "Testing pipelined encode/decode..."
& Get-Content "rand_test_file.bin" | $bitshuffle_bin --encode | $bitshuffle_bin --decode > "test_2.bin" | ForEach-Object {Write-Output "`toutput: $_";} *>&1
$ret1 = $?;
$test_hash_2 = (Get-FileHash -Algorithm SHA1 -Path "test_2.bin").Hash
$compare_result = ($rand_file_hash -eq $test_hash_2)

if ($ret1 -and $ret2 -and $compare_result) {
    Write-Output "Test succeeded."
} else {
    Write-Warning "Test failed."
    Write-Output "$rand_file_hash did not match $test_hash_1"
    $failed_tests = $failed_tests + 1;

    cat "rand_test_file.bin"
    cat "test_2.bin"
}

Write-Output "$failed_tests test failed"
exit $failed_tests;
