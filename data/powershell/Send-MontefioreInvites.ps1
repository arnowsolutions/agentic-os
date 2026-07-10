<#
.SYNOPSIS
    Outlook Calendar Bulk Invite Sender
    Creates and sends calendar invites via your local Outlook/Exchange session.
    
.DESCRIPTION
    This script uses Outlook COM automation to create calendar events with
    full HTML formatting (navy header, agenda table, Zoom button) and sends
    them as meeting requests through Exchange. Your Outlook handles the
    sending, so delivery to @montefiore.org is 100% reliable (internal Exchange).
    
    Test mode is ON by default — only sends to sfrasier@montefiore.org.
    When you're ready for production, set $script:TEST_MODE = $false below.

.NOTES
    Requires: Microsoft Outlook installed and logged in
    Run with: PowerShell (Run as Administrator not required)
    File: Send-MontefioreInvites.ps1
#>

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

# SET THIS TO $false WHEN YOU'RE READY FOR REAL SENDING
$script:TEST_MODE = $true
$script:TEST_EMAIL = "sfrasier@montefiore.org"

# Zoom links
$script:GR_ZOOM = "https://us02web.zoom.us/j/86773878358?pwd=RUxySVVzUjFWL0lyRWtjdDBacTVPZz09"
$script:GR_MEETING_ID = "867 7387 8358"
$script:GR_PASSCODE = "466916"

$script:MON_ZOOM = "https://montefiore.zoom.us/j/92009850717?pwd=25ask1SzLX2SdSrTbbhzb159UsyDFY.1"
$script:MON_MEETING_ID = "920 0985 0717"
$script:MON_PASSCODE = "808018"

# ═══════════════════════════════════════════════════════════════
# EVENTS DATA (from grand-rounds.js — academic year 2026-2027)
# ═══════════════════════════════════════════════════════════════
# Format: @{Date="YYYY-MM-DD"; Type="monday|grand-rounds"; Topic="..."; ...}

$script:EVENTS = @(

    # ═══════════════════════════
    # MONDAY SASP CONFERENCES
    # ═══════════════════════════
    @{Date="2026-07-06"; Type="monday"; Topic="SASP - UTI/STD/Infections"; Resident="Nate"; Attending="Edelblute"}
    @{Date="2026-07-13"; Type="monday"; Topic="SASP - Nephrolithiasis"; Resident="Jasmin"; Attending="Raskolnikov"}
    @{Date="2026-07-20"; Type="monday"; Topic="SASP - Trauma"; Resident="Dinora"; Attending="Donnelly"}
    @{Date="2026-07-27"; Type="monday"; Topic="SASP - Embryology"; Resident="Val"; Attending="Ohmann"}
    @{Date="2026-08-03"; Type="monday"; Topic="SASP - ED"; Resident="Sam"; Attending="Maria"}
    @{Date="2026-08-10"; Type="monday"; Topic="SASP - UDS"; Resident="N/A"; Attending="Abraham"}
    @{Date="2026-08-17"; Type="monday"; Topic="SASP - BPH/Obstructive Uropathy"; Resident="Jake"; Attending="Theofanides"}
    @{Date="2026-08-24"; Type="monday"; Topic="SASP - Neurogenic Bladder/Voiding Dysfunction"; Resident="Kelli"; Attending="Clearwater"}
    @{Date="2026-08-31"; Type="monday"; Topic="SASP - Urethral Reconstruction"; Resident="Rutul"; Attending="Cedars"}
    @{Date="2026-09-14"; Type="monday"; Topic="SASP - Infertility"; Resident="Joe"; Attending="Lipsky"}
    @{Date="2026-09-21"; Type="monday"; Topic="SASP - Adrenal Tumors"; Resident="Jen"; Attending="?"}
    @{Date="2026-09-28"; Type="monday"; Topic="SASP - UTUC"; Resident="Hordines"; Attending="Small"}
    @{Date="2026-10-05"; Type="monday"; Topic="SASP - NMIBC/MIBC"; Resident="Hill"; Attending="Sankin"}
    @{Date="2026-10-12"; Type="monday"; Topic="SASP - Renal Tumors"; Resident="Jasmin"; Attending="Aboumohamed"}
    @{Date="2026-10-19"; Type="monday"; Topic="SASP - Penile Cancer"; Resident="Dinora"; Attending="Lowe"}
    @{Date="2026-10-26"; Type="monday"; Topic="SASP - Testicular Tumors"; Resident="Nate"; Attending="Mallahan"}
    @{Date="2026-11-02"; Type="monday"; Topic="SASP - Prostate Cancer Workup/Treatment"; Resident="Sam"; Attending="Watts"}
    @{Date="2026-11-09"; Type="monday"; Topic="pre-ISE crash review"; Resident=""; Attending="Lipsky"}
    @{Date="2026-11-16"; Type="monday"; Topic="pre-ISE crash review"; Resident=""; Attending="Lowe"}
    @{Date="2026-11-23"; Type="monday"; Topic="post ise mental rest day"; Resident=""; Attending=""}
    @{Date="2026-11-30"; Type="monday"; Topic="SASP - Urinary Fistulae / Diversions"; Resident="Val"; Attending="Waldschmidtt"}
    @{Date="2026-12-07"; Type="monday"; Topic="SASP - Incontinence/OAB/POP"; Resident="Jake"; Attending="Laudano"}
    @{Date="2026-12-14"; Type="monday"; Topic="SASP - Lap/Robotic Surgery"; Resident="Joe"; Attending="Edelblute"}
    @{Date="2026-12-21"; Type="monday"; Topic="SASP - Physiology (fluids, electrolytes, HTN/vascular disease, endocrinopathy)"; Resident="Kelli"; Attending="Donnelly"}
    @{Date="2027-01-04"; Type="monday"; Topic="SASP - Pediatric GU Onc"; Resident="Rutul"; Attending="Ohmann"}
    @{Date="2027-01-11"; Type="monday"; Topic="SASP - Congenital Anomalies"; Resident="Hordines"; Attending="Raskolnikov"}
    @{Date="2027-01-25"; Type="monday"; Topic="SASP -"; Resident="Hill"; Attending=""}
    @{Date="2027-02-01"; Type="monday"; Topic="SASP"; Resident="Pak"; Attending=""}
    @{Date="2027-02-08"; Type="monday"; Topic="SASP"; Resident=""; Attending=""}
    @{Date="2027-02-15"; Type="monday"; Topic="SASP"; Resident=""; Attending=""}
    @{Date="2027-03-01"; Type="monday"; Topic="SASP"; Resident=""; Attending=""}
    @{Date="2027-03-08"; Type="monday"; Topic="SASP"; Resident=""; Attending=""}
    @{Date="2027-03-15"; Type="monday"; Topic="SASP"; Resident=""; Attending=""}
    @{Date="2027-03-22"; Type="monday"; Topic="SASP"; Resident=""; Attending=""}
    @{Date="2027-03-29"; Type="monday"; Topic="SASP"; Resident=""; Attending=""}
    @{Date="2027-04-05"; Type="monday"; Topic="SASP"; Resident=""; Attending=""}
    @{Date="2027-04-12"; Type="monday"; Topic="SASP"; Resident=""; Attending=""}
    @{Date="2027-04-19"; Type="monday"; Topic="SASP"; Resident=""; Attending=""}
    @{Date="2027-04-26"; Type="monday"; Topic="SASP"; Resident=""; Attending=""}
    @{Date="2027-05-03"; Type="monday"; Topic="SASP -"; Resident=""; Attending=""}
    @{Date="2027-05-10"; Type="monday"; Topic="SASP -"; Resident=""; Attending=""}
    @{Date="2027-05-17"; Type="monday"; Topic="SASP -"; Resident=""; Attending=""}
    @{Date="2027-05-24"; Type="monday"; Topic="SASP -"; Resident=""; Attending=""}
    @{Date="2027-06-07"; Type="monday"; Topic="SKIT"; Resident=""; Attending=""}
    @{Date="2027-06-14"; Type="monday"; Topic="SKIT"; Resident=""; Attending=""}
    @{Date="2027-06-21"; Type="monday"; Topic="End of year debrief"; Resident=""; Attending=""}
    @{Date="2027-06-28"; Type="monday"; Topic="Expectations Meeting"; Resident=""; Attending=""}

    # ═══════════════════════════
    # FRIDAY GRAND ROUNDS
    # ═══════════════════════════
    @{Date="2026-07-10"; Type="grand-rounds"; MeetingType="Peds Grand Rounds"; Topic7="Peds"; Topic8="Peds Multidisciplinary"}
    @{Date="2026-07-17"; Type="grand-rounds"; MeetingType="Grand Rounds"; Topic7="Sankin expectations overview (1hr)"; Topic8="Sub-I talks - 0.75 hr (3)"}
    @{Date="2026-07-31"; Type="grand-rounds"; MeetingType="QI"; Topic7="Quality Improvement: Stats/M&Ms/Indications June/ July"; Topic8=""}
    @{Date="2026-08-07"; Type="grand-rounds"; MeetingType="Grand Rounds"; Topic7="SASP Review with Dr. Lipsky"; Topic8=""}
    @{Date="2026-08-14"; Type="grand-rounds"; MeetingType="Grand Rounds"; Topic7=""; Topic8="Sub-I talks - 0.5 hr (2)"}
    @{Date="2026-08-28"; Type="grand-rounds"; MeetingType="Grand Rounds"; Topic7="PGY-4 Subspeciality Presentations"; Topic8="Sub-I talks - 0.75 hr (3)"}
    @{Date="2026-09-11"; Type="grand-rounds"; MeetingType="Peds Grand Rounds"; Topic7="Peds"; Topic8="Peds Multidisciplinary"}
    @{Date="2026-09-18"; Type="grand-rounds"; MeetingType="Faculty Meeting"; Topic7="FACULTY MEETING"; Topic8=""}
    @{Date="2026-09-25"; Type="grand-rounds"; MeetingType="Grand Rounds"; Topic7=""; Topic8="Sub-I talks - 0.75 hr (3)"}
    @{Date="2026-10-02"; Type="grand-rounds"; MeetingType="QI"; Topic7="Quality Improvement: Stats/M&Ms/Indications Aug/ Sept"; Topic8=""}
    @{Date="2026-10-09"; Type="grand-rounds"; MeetingType="Peds Grand Rounds"; Topic7="Peds"; Topic8="Peds Multidisciplinary"}
    @{Date="2026-10-23"; Type="grand-rounds"; MeetingType="Grand Rounds"; Topic7="Sub-Intern Presentations - 1 hr (4)"; Topic8=""}
    @{Date="2026-10-30"; Type="grand-rounds"; MeetingType="Grand Rounds"; Topic7=""; Topic8="PGY-4 Subspeciality Presentations"}
    @{Date="2026-11-06"; Type="grand-rounds"; MeetingType="Faculty Meeting"; Topic7="FACULTY MEETING"; Topic8=""}
    @{Date="2026-11-13"; Type="grand-rounds"; MeetingType="Peds Grand Rounds"; Topic7="Peds"; Topic8="Peds Multidisciplinary"}
    @{Date="2026-12-04"; Type="grand-rounds"; MeetingType="QI"; Topic7="Quality Improvement: Stats/M&Ms/Indications Oct-Nov"; Topic8=""}
    @{Date="2026-12-11"; Type="grand-rounds"; MeetingType="Peds Grand Rounds"; Topic7="Peds"; Topic8="Peds Multidisciplinary"}
    @{Date="2026-12-18"; Type="grand-rounds"; MeetingType="Grand Rounds"; Topic7="Valentine Essay Submission Presentations"; Topic8="Resident QI Updates"}
    @{Date="2027-01-08"; Type="grand-rounds"; MeetingType="Peds Grand Rounds"; Topic7="Peds"; Topic8="Peds Multidisciplinary"}
    @{Date="2027-01-15"; Type="grand-rounds"; MeetingType="Faculty Meeting"; Topic7="FACULTY MEETING"; Topic8=""}
    @{Date="2027-01-22"; Type="grand-rounds"; MeetingType="Journal Club"; Topic7="Journal Club"; Topic8=""}
    @{Date="2027-02-05"; Type="grand-rounds"; MeetingType="QI"; Topic7="Quality Improvement: Stats/M&Ms/Indications - Dec/Jan"; Topic8=""}
    @{Date="2027-02-12"; Type="grand-rounds"; MeetingType="Peds Grand Rounds"; Topic7="Peds"; Topic8="Peds Multidisciplinary"}
    @{Date="2027-02-19"; Type="grand-rounds"; MeetingType="Grand Rounds"; Topic7="PGY-4 Subspeciality Presentations (1 hr)"; Topic8="Visiting Lecture: Fed Ghali (Yale) - Uro-oncology"}
    @{Date="2027-02-26"; Type="grand-rounds"; MeetingType="Grand Rounds"; Topic7="Prisoner Ethics - Ari"; Topic8="Prisoner Ethics - Small"}
    @{Date="2027-03-05"; Type="grand-rounds"; MeetingType="Faculty Meeting"; Topic7="FACULTY MEETING"; Topic8=""}
    @{Date="2027-03-12"; Type="grand-rounds"; MeetingType="Peds Grand Rounds"; Topic7="Peds"; Topic8="Peds Multidisciplinary"}
    @{Date="2027-03-19"; Type="grand-rounds"; MeetingType="Journal Club"; Topic7="Journal Club"; Topic8=""}
    @{Date="2027-03-26"; Type="grand-rounds"; MeetingType="QI"; Topic7="Quality Improvement: Stats/M&Ms/Indications - Feb/ March"; Topic8="Sub-I Presentation (1 - 15 min)"}
    @{Date="2027-04-09"; Type="grand-rounds"; MeetingType="Peds Grand Rounds"; Topic7="Peds"; Topic8="Peds Multidisciplinary"}
    @{Date="2027-04-16"; Type="grand-rounds"; MeetingType="Grand Rounds"; Topic7="Guest Speaker - Contract Negotiations"; Topic8="Prosthetics Talk - Dr. Pedro Maria"}
    @{Date="2027-04-23"; Type="grand-rounds"; MeetingType="Grand Rounds"; Topic7="Sub-I Presentation (15 min)/PGY 4 Subspecialty"; Topic8="Dr Kelvin Davies - Testing a Paradigm Shift"}
    @{Date="2027-04-30"; Type="grand-rounds"; MeetingType="QI"; Topic7="Quality Improvement: Stats/M&Ms/Indications - March/April"; Topic8=""}
    @{Date="2027-05-07"; Type="grand-rounds"; MeetingType="Peds Grand Rounds"; Topic7="Peds"; Topic8="Peds Multidisciplinary"}
    @{Date="2027-05-28"; Type="grand-rounds"; MeetingType="Journal Club"; Topic7="Journal Club/ STATs with Dr. Aggaliu"; Topic8=""}
    @{Date="2027-06-04"; Type="grand-rounds"; MeetingType="QI"; Topic7="Quality Improvement: Stats/M&Ms/Indications - May"; Topic8=""}
    @{Date="2027-06-11"; Type="grand-rounds"; MeetingType="Peds Grand Rounds"; Topic7="Dr. Kryger VP"; Topic8="Peds Multidisciplinary"}
    @{Date="2027-06-25"; Type="grand-rounds"; MeetingType="Faculty Meeting"; Topic7="FACULTY MEETING"; Topic8=""}
)

# ═══════════════════════════════════════════════════════════════
# RECIPIENT EMAIL LISTS (from email_groups.json)
# ═══════════════════════════════════════════════════════════════

$script:RECIPIENTS = @{
    resident_conference = @(
        "dmurota@montefiore.org",
        "jdrobner@montefiore.org",
        "jcapellan@montefiore.org",
        "johill@montefiore.org",
        "johordines@montefiore.org",
        "jkim28@montefiore.org",
        "kaibel@montefiore.org",
        "niskhakov@montefiore.org",
        "rutupatel@montefiore.org",
        "syim@montefiore.org",
        "sopak@montefiore.org",
        "valpatel@montefiore.org",
        "lsantosmol@montefiore.org",
        "matantonel@montefiore.org",
        "eskim@montefiore.org"
    )
    faculty = @(
        "aaboumoh@montefiore.org",
        "asankin@montefiore.org",
        "alesmall@montefiore.org",
        "bcedars@montefiore.org",
        "bedelblute@montefiore.org",
        "cmallahan@montefiore.org",
        "draskolnik@montefiore.org",
        "eohmann@montefiore.org",
        "flowe@montefiore.org",
        "jdonnelly@montefiore.org",
        "kwatts@montefiore.org",
        "kbottger@montefiore.org",
        "mtheofanid@montefiore.org",
        "mschoenb@montefiore.org",
        "mdanzig@montefiore.org",
        "Melissa.Laudano@einsteinmed.edu",
        "mlipsky@montefiore.org",
        "mharel@montefiore.org",
        "nabraham@montefiore.org",
        "nwaldschmi@montefiore.org",
        "pmaria@montefiore.org",
        "sboczko@montefiore.org",
        "wclearwa@montefiore.org"
    )
}

# Combined grand_rounds list = faculty + residents
$script:RECIPIENTS.grand_rounds = $script:RECIPIENTS.faculty + @(
    "azallen@montefiore.org",
    "akasharma@montefiore.org",
    "adelvlahos@montefiore.org",
    "anorth@montefiore.org",
    "aasencio@montefiore.org",
    "aalaimo@montefiore.org",
    "avarughe@montefiore.org",
    "ashperdhej@montefiore.org",
    "arkrishnan@montefiore.org",
    "bgartrel@montefiore.org",
    "cdove@montefiore.org",
    "crysantos@montefiore.org",
    "dosulli@montefiore.org",
    "dkarki@montefiore.org",
    "dmurota@montefiore.org",
    "fkassam@montefiore.org",
    "hkanakka@montefiore.org",
    "hmelo@montefiore.org",
    "hmary@montefiore.org",
    "ilir.agalliu@einsteinmed.edu",
    "jdrobner@montefiore.org",
    "jcapellan@montefiore.org",
    "jdiazgonza@montefiore.org",
    "johill@montefiore.org",
    "johordines@montefiore.org",
    "jkim28@montefiore.org",
    "joodume@montefiore.org",
    "jcollazo@montefiore.org",
    "karamire@montefiore.org",
    "kaibel@montefiore.org",
    "kelvin.davies@einsteinmed.edu",
    "kmehta@montefiore.org",
    "mgarg@montefiore.org",
    "mbagcal@montefiore.org",
    "mohara@montefiore.org",
    "mnwhite@montefiore.org",
    "nadchowdhu@montefiore.org",
    "niskhakov@montefiore.org",
    "solsjon@montefiore.org",
    "pakeatle@montefiore.org",
    "pkareth@montefiore.org",
    "rheredia@montefiore.org",
    "rutupatel@montefiore.org",
    "sasaji@montefiore.org",
    "sarodrigue@montefiore.org",
    "syim@montefiore.org",
    "skalnick@montefiore.org",
    "sfrasier@montefiore.org",
    "sipappac@montefiore.org",
    "sopak@montefiore.org",
    "sbalcarr@montefiore.org",
    "sylvia.suadicani@einsteinmed.edu",
    "tafergus@montefiore.org",
    "tnardi@montefiore.org",
    "valpatel@montefiore.org",
    "wbodner@montefiore.org",
    "yduchein@montefiore.org",
    "wwint@montefiore.org",
    "marisoto@montefiore.org",
    "swiafe@montefiore.org",
    "equiachon@montefiore.org",
    "midejes@montefiore.org",
    "lsantosmol@montefiore.org",
    "matantonel@montefiore.org",
    "eskim@montefiore.org"
) | Select-Object -Unique

# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

function Get-DayOfWeek {
    param([string]$DateStr)
    $d = [datetime]::ParseExact($DateStr, "yyyy-MM-dd", $null)
    return $d.ToString("dddd")
}

function Get-FormattedDate {
    param([string]$DateStr)
    $d = [datetime]::ParseExact($DateStr, "yyyy-MM-dd", $null)
    return $d.ToString("dddd, MMMM dd, yyyy")
}

function Get-MondaySubject {
    param($Event)
    $topic = $Event.Topic
    $attending = $Event.Attending
    if ($attending) {
        return "Invitation: Urology Monday Conference - $topic, Dr. $attending"
    }
    return "Invitation: Urology Monday Conference - $topic"
}

function Get-MondayHTMLBody {
    param($Event)
    $topic = $Event.Topic
    $resident = $Event.Resident
    $attending = $Event.Attending
    $date = Get-FormattedDate $Event.Date
    
    return @"
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background-color:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f3f4f6;padding:20px">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08)">
<tr><td style="background:#1a3a5c;padding:20px 40px;text-align:center">
<h1 style="margin:0;color:#ffffff;font-size:18px;font-weight:700">Montefiore Urology</h1>
<p style="margin:4px 0 0 0;color:rgba(255,255,255,0.80);font-size:13px">Resident AM Conference</p>
</td></tr>
<tr><td style="padding:24px 40px">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f7ff;border:1px solid #bfdbfe;border-radius:8px;margin-bottom:16px">
<tr><td style="padding:16px 20px;text-align:center">
<p style="margin:0 0 12px 0;font-size:11px;color:#1d4ed8;font-weight:600;text-transform:uppercase;letter-spacing:0.5px">Zoom Meeting</p>
<a href="$script:MON_ZOOM" style="display:inline-block;background-color:#1a3a5c;color:#ffffff;font-size:13px;font-weight:600;text-decoration:none;padding:10px 24px;border-radius:6px">Click Here to Join Zoom Meeting →</a>
<table cellpadding="0" cellspacing="0" style="margin:0 auto">
<tr><td style="font-size:12px;color:#6b7280;padding:2px 8px 2px 0">Meeting ID:</td><td style="font-size:13px;color:#111827;font-weight:600">$script:MON_MEETING_ID</td></tr>
<tr><td style="font-size:12px;color:#6b7280;padding:2px 8px 2px 0">Passcode:</td><td style="font-size:13px;color:#111827;font-weight:600">$script:MON_PASSCODE</td></tr>
</table>
</td></tr>
</table>
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;margin-bottom:16px">
<tr><td style="padding:12px 16px;font-size:11px;color:#6b7280;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;border-bottom:1px solid #e5e7eb;text-align:center">Details</td></tr>
<tr><td style="padding:14px 20px;text-align:center">
<p style="margin:0 0 4px 0;font-size:14px;color:#111827;font-weight:500"><strong>Topic:</strong> $topic</p>
<p style="margin:4px 0;font-size:14px;color:#374151"><strong>Date:</strong> $date</p>
<p style="margin:4px 0;font-size:14px;color:#374151"><strong>Time:</strong> 7:00 – 8:00 AM (EDT)</p>
<p style="margin:4px 0;font-size:14px;color:#374151"><strong>Resident:</strong> $(if($resident){"Dr. $resident"}else{"TBD"})</p>
<p style="margin:4px 0 0 0;font-size:14px;color:#374151"><strong>Attending:</strong> $(if($attending){"Dr. $attending"}else{"TBD"})</p>
</td></tr>
</table>
</td></tr>
<tr><td style="background:#f9fafb;padding:16px 40px;text-align:center;border-top:1px solid #e5e7eb">
<p style="margin:0;font-size:11px;color:#9ca3af">Montefiore Medical Center · Department of Urology</p>
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>
"@
}

function Get-GRSubject {
    param($Event)
    $mt = $Event.MeetingType
    $t7 = $Event.Topic7
    $t8 = $Event.Topic8
    if ($mt -eq "Faculty Meeting") { return "Invitation: [FACULTY] Faculty Meeting" }
    if ($mt -eq "Peds Grand Rounds") { return "Invitation: Urology Grand Rounds - Peds / Peds Multidisciplinary" }
    if ($mt -eq "Journal Club") { return "Invitation: Urology Grand Rounds - Journal Club" }
    $topics = @($t7, $t8) | Where-Object { $_ } | Select-Object -Unique
    $topicStr = $topics -join " / "
    if ($topicStr) { return "Invitation: Urology Grand Rounds - $topicStr" }
    return "Invitation: Urology Grand Rounds"
}

function Get-GRHTMLBody {
    param($Event)
    $mt = $Event.MeetingType
    $t7 = $Event.Topic7
    $t8 = $Event.Topic8
    $date = Get-FormattedDate $Event.Date
    $summary = (Get-GRSubject $Event) -replace "^Invitation: ", ""
    
    $agendaRows = ""
    if ($t7) {
        $agendaRows += @"
<tr><td style="padding:14px 20px;$((if($t8){'border-bottom:1px solid #e5e7eb;'})else{''})text-align:center">
<p style="margin:0;font-size:11px;color:#6b7280;font-weight:600;text-transform:uppercase;letter-spacing:0.5px">Grand Rounds</p>
<p style="margin:2px 0 0 0;font-size:12px;color:#9ca3af">7:00 – 8:00 AM</p>
<p style="margin:6px 0 0 0;font-size:14px;color:#111827;font-weight:500">$t7</p>
</td></tr>
"@
    }
    if ($t8 -and $t8 -ne $t7) {
        $agendaRows += @"
<tr><td style="padding:14px 20px;text-align:center">
<p style="margin:0;font-size:11px;color:#6b7280;font-weight:600;text-transform:uppercase;letter-spacing:0.5px">Grand Rounds Conference</p>
<p style="margin:2px 0 0 0;font-size:12px;color:#9ca3af">8:00 – 9:00 AM</p>
<p style="margin:6px 0 0 0;font-size:14px;color:#111827;font-weight:500">$t8</p>
</td></tr>
"@
    }
    
    return @"
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background-color:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f3f4f6;padding:20px">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08)">
<tr><td style="background:#1a3a5c;padding:20px 40px;text-align:center">
<h1 style="margin:0;color:#ffffff;font-size:18px;font-weight:700">Montefiore Urology</h1>
<p style="margin:4px 0 0 0;color:rgba(255,255,255,0.80);font-size:13px">$summary</p>
</td></tr>
<tr><td style="padding:24px 40px">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f7ff;border:1px solid #bfdbfe;border-radius:8px;margin-bottom:16px">
<tr><td style="padding:16px 20px;text-align:center">
<p style="margin:0 0 12px 0;font-size:11px;color:#1d4ed8;font-weight:600;text-transform:uppercase;letter-spacing:0.5px">Zoom Meeting</p>
<a href="$script:GR_ZOOM" style="display:inline-block;background-color:#1a3a5c;color:#ffffff;font-size:13px;font-weight:600;text-decoration:none;padding:10px 24px;border-radius:6px">Click Here to Join Zoom Meeting →</a>
<table cellpadding="0" cellspacing="0" style="margin:0 auto">
<tr><td style="font-size:12px;color:#6b7280;padding:2px 8px 2px 0">Meeting ID:</td><td style="font-size:13px;color:#111827;font-weight:600">$script:GR_MEETING_ID</td></tr>
<tr><td style="font-size:12px;color:#6b7280;padding:2px 8px 2px 0">Passcode:</td><td style="font-size:13px;color:#111827;font-weight:600">$script:GR_PASSCODE</td></tr>
</table>
</td></tr>
</table>
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;margin-bottom:16px">
<tr><td style="padding:12px 16px;font-size:11px;color:#6b7280;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;border-bottom:1px solid #e5e7eb;text-align:center">Agenda</td></tr>
$agendaRows
</table>
<table width="100%" cellpadding="0" cellspacing="0">
<tr><td style="padding:8px 0;text-align:center">
<p style="margin:0;font-size:14px;color:#374151"><strong>Date:</strong> $date</p>
<p style="margin:6px 0 0 0;font-size:14px;color:#374151"><strong>Time:</strong> 7:00 – 9:00 AM (EDT)</p>
</td></tr>
</table>
</td></tr>
<tr><td style="background:#f9fafb;padding:16px 40px;text-align:center;border-top:1px solid #e5e7eb">
<p style="margin:0;font-size:11px;color:#9ca3af">Montefiore Medical Center · Department of Urology</p>
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>
"@
}

function Get-Recipients {
    param($Event)
    if ($script:TEST_MODE) { return @($script:TEST_EMAIL) }
    
    if ($Event.Type -eq "monday") { return $script:RECIPIENTS.resident_conference }
    
    $mt = $Event.MeetingType
    if ($mt -eq "Faculty Meeting") { return $script:RECIPIENTS.faculty }
    return $script:RECIPIENTS.grand_rounds
}

# ═══════════════════════════════════════════════════════════════
# MAIN SENDING FUNCTION
# ═══════════════════════════════════════════════════════════════

function Send-CalendarInvite {
    param($Event)
    
    try {
        $outlook = New-Object -ComObject Outlook.Application
        $appointment = $outlook.CreateItem(1)  # 1 = olAppointmentItem
        
        # Set meeting type
        $appointment.MeetingStatus = 1  # 1 = olMeeting
        $appointment.ReminderSet = $true
        $appointment.ReminderMinutesBeforeStart = 15
        
        # Parse date/time
        if ($Event.Type -eq "monday") {
            $startTime = "07:00"
            $endTime = "08:00"
            $appointment.Subject = Get-MondaySubject $Event
            $appointment.Body = Get-MondayHTMLBody $Event
        } else {
            $startTime = "07:00"
            $endTime = "09:00"
            $appointment.Subject = Get-GRSubject $Event
            $appointment.Body = Get-GRHTMLBody $Event
        }
        
        $startDt = [datetime]::ParseExact("$($Event.Date) $startTime", "yyyy-MM-dd HH:mm", $null)
        $endDt = [datetime]::ParseExact("$($Event.Date) $endTime", "yyyy-MM-dd HH:mm", $null)
        
        $appointment.Start = $startDt
        $appointment.End = $endDt
        $appointment.Location = "Zoom"
        $appointment.AllDayEvent = $false
        
        # Set HTML body
        $appointment.BodyFormat = 2  # 2 = olFormatHTML
        
        # Add recipients
        $recipients = Get-Recipients $Event
        foreach ($email in $recipients) {
            if ($email -and $email.Trim()) {
                $recip = $appointment.Recipients.Add($email.Trim())
                $recip.Type = 1  # 1 = olRequired
            }
        }
        
        # Send
        $appointment.Send()
        return $true, ""
    }
    catch {
        return $false, $_.Exception.Message
    }
}

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

Write-Host "╔══════════════════════════════════════════════════════════════╗"
Write-Host "║     Montefiore Urology — Outlook Bulk Invite Sender      ║"
Write-Host "╚══════════════════════════════════════════════════════════════╝"
Write-Host ""

if ($script:TEST_MODE) {
    Write-Host "🔵 TEST MODE: All invites will go ONLY to $($script:TEST_EMAIL)" -ForegroundColor Cyan
    Write-Host "   Set `$TEST_MODE = `$false in the script to send to real recipients.`n" -ForegroundColor Yellow
} else {
    Write-Host "🔴 PRODUCTION MODE: Invites will go to all residents/faculty!" -ForegroundColor Red
    Write-Host "   Press Ctrl+C now to cancel, or wait 5 seconds to continue...`n" -ForegroundColor Yellow
    Start-Sleep -Seconds 5
}

$totalEvents = $script:EVENTS.Count
$sentCount = 0
$failCount = 0
$failedDates = @()

Write-Host "Processing $totalEvents events...`n" -ForegroundColor Green

for ($i = 0; $i -lt $totalEvents; $i++) {
    $ev = $script:EVENTS[$i]
    $displayDate = Get-Date $ev.Date -Format "MMM dd"
    $displayDay = Get-DayOfWeek $ev.Date
    $eventNum = $i + 1
    
    if ($ev.Type -eq "monday") {
        $desc = "Mon SASP: $($ev.Topic)"
    } else {
        $desc = "$($ev.MeetingType): $($ev.Topic7) / $($ev.Topic8)"
    }
    
    Write-Progress -Activity "Sending calendar invites..." -Status "$eventNum of $totalEvents" -PercentComplete (($i / $totalEvents) * 100)
    
    Write-Host "[$eventNum/$totalEvents] $displayDate ($displayDay) - " -NoNewline
    Write-Host "$desc" -NoNewline
    
    $ok, $err = Send-CalendarInvite $ev
    
    if ($ok) {
        Write-Host " ✅" -ForegroundColor Green
        $sentCount++
    } else {
        Write-Host " ❌ $err" -ForegroundColor Red
        $failCount++
        $failedDates += "$($ev.Date): $err"
    }
    
    # Small delay between sends
    if ($i -lt $totalEvents - 1) { Start-Sleep -Milliseconds 500 }
}

Write-Progress -Activity "Done" -Completed
Write-Host "`n══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "SUMMARY:" -ForegroundColor Cyan
Write-Host "  Total: $totalEvents events"
Write-Host "  Sent:  $sentCount ✅" -ForegroundColor $(if($sentCount -gt 0){'Green'}else{'White'})
Write-Host "  Failed: $failCount" -ForegroundColor $(if($failCount -gt 0){'Red'}else{'White'})

if ($failedDates.Count -gt 0) {
    Write-Host "`n  Failed events:" -ForegroundColor Red
    foreach ($f in $failedDates) { Write-Host "    ❌ $f" -ForegroundColor Red }
}

if ($script:TEST_MODE) {
    Write-Host "`n⚠  TEST MODE was ON — no real sends happened." -ForegroundColor Yellow
    Write-Host "   When you're ready, set `$TEST_MODE = `$false at the top of this script." -ForegroundColor Yellow
}

Write-Host "`nDone!" -ForegroundColor Green
