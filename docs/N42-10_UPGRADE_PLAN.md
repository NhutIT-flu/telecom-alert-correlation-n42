# N42-10 ? n?ng c?p ng?y 13/11/2026

Owner: Ng? Ch?u Ki?t (QA). Ng??i d?ng cho ph?p tri?n khai 9 h?ng m?c v? d?ng lab ?? sao l?u. Ch? TL review tr??c merge. Ngu?n: Jira N42-10, TC-OPS-002, AC-07/08 v? review PR #17.

## Ca nghi?m thu b? sung (??c t? tr??c tri?n khai)

| ID | Input/?i?u ki?n | Expected |
|---|---|---|
| CI-09 | Push feature ho?c PR main c? test m?i trong tests/test_*.py | Checkout revision nh?nh/merge ref, ch?y to?n b? unittest + pytest; JUnit/coverage g?n SHA |
| CI-10 | M?t test backend th?t b?i | tests/check t?ng h?p ??; merge ch? b? ch?n khi required check ?? b?t |
| JK-01 | Build main ho?c job review d?ng project validation c? ??nh | Scanner v? Gate c?ng task/revision, kh?ng ghi ?? project ch?nh t? feature |
| JK-02 | Gate tr? OK / ERROR | SUCCESS / FAILURE v? artifact Gate |
| JK-03 | B??c wait th?c s? h?t deadline | FAILURE, artifact TIMEOUT; h?y th? c?ng v?n ABORTED |
| OPS-04 | Backup khi Jenkins/Sonar d?ng, PostgreSQL dump, archive volume | Ki?m checksum, danh m?c archive v? restore th? database/Jenkins tr?n volume c?ch ly |
| OPS-05 | Restart stack v?i volume ?? x?c minh | Job/config/project/database c?n; kh?ng t? t?o volume tr?ng |

## Ph?m vi quy?n

Kh?ng t? merge PR, ??i policy owner, ??ng Jira ho?c tuy?n b? required checks ho?t ??ng khi thi?u quy?n. Gi? c?c stash N42-12. Main polling ch? x?c minh sau merge ???c duy?t. Kh?ng th?m t? ??ng g?i Jira/email.
