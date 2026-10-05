<?php
/* Nordpflege24: receives a request from the question form and mails it to the Nordpflege24 mailbox.
   Runs on the same server as the website (netcup, Germany). Nothing is stored on the server and nothing leaves it
   except the one e-mail to the mailbox below. Answers with JSON: {"success":true} or {"success":false}. */

declare(strict_types=1);

const RECIPIENT = 'kontakt@nordpflege24.de';
const SENDER    = 'kontakt@nordpflege24.de';
const SITE_HOST = 'nordpflege24.de';

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');

function answer(bool $ok, int $status = 200): void {
    http_response_code($status);
    echo json_encode(['success' => $ok]);
    exit;
}

/* One line of text: no control characters, trimmed, cut to a sane length. */
function field(string $key, int $max = 200): string {
    $v = $_POST[$key] ?? '';
    if (!is_string($v)) return '';
    $v = preg_replace('/[\x00-\x1F\x7F]+/u', ' ', $v) ?? '';
    return mb_substr(trim($v), 0, $max);
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') answer(false, 405);

/* Only the website itself may send: the browser states where the request comes from. */
$origin = $_SERVER['HTTP_ORIGIN'] ?? ($_SERVER['HTTP_REFERER'] ?? '');
$host = strtolower((string) parse_url($origin, PHP_URL_HOST));
if ($host !== SITE_HOST && $host !== 'www.' . SITE_HOST) answer(false, 403);

/* Hidden field that people never fill in. Bots do; they get a friendly yes and no e-mail is sent. */
if (field('_gotcha') !== '') answer(true);

$forms = [
    'pflege-anfrage' => ['title' => 'Pflege-Anfrage', 'rows' => ['fuer' => 'Für wen', 'bedarf' => 'Bedarf', 'ort' => 'PLZ oder Ort']],
    'job-anfrage'    => ['title' => 'Job-Anfrage',    'rows' => ['ausbildung' => 'Ausbildung', 'umfang' => 'Umfang', 'ort' => 'PLZ oder Ort']],
];
$form = field('formular', 40);
if (!isset($forms[$form])) answer(false, 422);

$vorname  = field('vorname', 80);
$nachname = field('nachname', 80);
$telefon  = field('telefon', 40);
$email    = field('email', 120);

/* Same checks as in the browser. Without both consents nothing is sent. */
$valid = $vorname !== '' && $nachname !== ''
    && strlen(preg_replace('/\D/', '', $telefon) ?? '') >= 6
    && filter_var($email, FILTER_VALIDATE_EMAIL) !== false
    && field('einwilligung', 10) === 'ja'
    && strpos(field('agb', 40), 'ja') === 0;
if (!$valid) answer(false, 422);

$lines = [$forms[$form]['title'] . ' über nordpflege24.de', ''];
foreach ($forms[$form]['rows'] as $key => $label) {
    $lines[] = $label . ': ' . field($key, 300);
}
$lines[] = '';
$lines[] = 'Vorname: ' . $vorname;
$lines[] = 'Nachname: ' . $nachname;
$lines[] = 'Telefon: ' . $telefon;
$lines[] = 'E-Mail: ' . $email;
$lines[] = '';
$lines[] = 'Einwilligung: ' . field('einwilligung', 10);
$lines[] = 'Zeitpunkt (Browser): ' . field('einwilligung_zeit', 40);
$lines[] = 'Zeitpunkt (Server): ' . gmdate('Y-m-d\TH:i:s\Z');
$lines[] = 'AGB: ' . field('agb', 40);
$lines[] = 'Wortlaut der Einwilligung: ' . field('einwilligung_text', 900);

$subject = $forms[$form]['title'] . ': ' . $vorname . ' ' . $nachname . ' (' . field('ort', 60) . ')';
$headers = [
    'From'         => 'Nordpflege24 Formular <' . SENDER . '>',
    'Reply-To'     => $email,
    'MIME-Version' => '1.0',
    'Content-Type' => 'text/plain; charset=UTF-8',
    'Content-Transfer-Encoding' => '8bit',
];

$sent = mail(RECIPIENT, mb_encode_mimeheader($subject, 'UTF-8', 'B'), implode("\r\n", $lines), $headers, '-f' . SENDER);
answer($sent, $sent ? 200 : 500);
