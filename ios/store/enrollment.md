# Apple Developer Program: enrolling MAGMACRUNCH MEDIA LLC

The details Apple and Dun & Bradstreet will ask for, in one place, because
the usual reason an enrollment stalls is the same string typed three ways.
D&B's record, Apple's enrollment form and the App Store listing all have to
agree, and Apple compares them.

Checked against Apple's own pages on 2026-09-19:
`developer.apple.com/support/D-U-N-S/` and
`developer.apple.com/help/account/membership/program-enrollment`.

## What is fixed

| | |
|---|---|
| Legal entity name | `MAGMACRUNCH MEDIA LLC`, as registered in Pennsylvania. Exactly as the state has it, including `LLC` and its spacing. |
| Seller name on the App Store | The legal entity name, so `MAGMACRUNCH MEDIA LLC`. This is the whole reason for enrolling as an organization: an individual enrollment lists a personal legal name instead, and needs neither a D-U-N-S Number nor an address on the domain. Weighed and settled on 2026-09-19: the organization route, knowing that converting afterwards means going back to Apple rather than ticking a box. |
| Website | `https://magmacrunch.com`. Apple requires it to be publicly available, functional, and on a domain associated with the organization. It is, and it now links to the game, the privacy page and the support page. |
| Binding authority | The owner. Apple requires whoever enrolls to be able to bind the company to agreements. |
| Cost | The program is $99/year. A D-U-N-S Number is free. |

## What is outstanding

1. **A D-U-N-S Number.** Requested 2026-09-19 through Apple's own lookup at
   `developer.apple.com/enroll/duns-lookup/`, which is the door to use: D&B may
   already hold a record for a registered LLC, and the same page requests one
   when it does not. D&B answered that the number has been sent to the contact
   email. Allow up to 5 business days for it and up to 2 more for Apple to see
   it; paying to expedite does not shorten it. Give Apple D&B's exact spelling
   afterwards, including the comma D&B inserts before `LLC` that the
   Pennsylvania registration does not have.

2. **A work email address on `magmacrunch.com`.** Apple: "Your work email
   address needs to be associated with your organization's domain name." The
   domain had no MX records at all (checked 2026-09-19), so there was no mailbox
   to use. This is the piece most likely to be discovered late, because
   everything else about the company is already in order.

   Forwarding rather than a mailbox: ImprovMX on its free tier, with `jake@` and
   `info@` created 2026-09-19 and pointing at the Gmail account. That needs two
   MX records and nothing else. The SPF record ImprovMX also shows matters for
   *sending* as the domain, which the free tier does not do.

   ```
   @  MX  10  mx1.improvmx.com.
   @  MX  20  mx2.improvmx.com.
   ```

   Added 2026-09-19 and live the same minute, confirmed by query against both
   8.8.8.8 and 1.1.1.1. The second record's preference reads 28 rather than 20,
   a typo that changes nothing: preference only orders which server is tried
   first. What remains is a delivery test, since records resolving and mail
   arriving are different claims.

   **Where to add them cost an evening, and the answer is boring: Squarespace,
   under Domains, magmacrunch.com, DNS, DNS Settings, Custom records.** Two
   things sent this the wrong way, and both look like evidence:

   ```
   nameservers           = ns-cloud-a1..a4.googledomains.com
   responsible mail addr = cloud-dns-hostmaster.google.com
   ```

   Neither means Google Cloud. Squarespace bought Google Domains and kept
   running on the infrastructure it acquired, so a zone managed entirely from
   the Squarespace panel still answers with Google's nameserver names and
   Google's SOA contact. **There is no Google Cloud project, and
   `console.cloud.google.com` is a dead end**: it offers to enable the Cloud DNS
   API, which reads like a permissions problem and is really the console saying
   there is nothing here.

   The test that would have settled it in one step is the records themselves.
   Squarespace's DNS Settings page listed nine records, and all nine, including
   eight obscure board-game subdomains pointing at a machine that is not the
   website, resolved live to exactly those values. An editor showing what DNS actually answers is the live
   editor. Compare the panel against `nslookup` before theorising about who
   serves the zone.

   Delivery verified 2026-09-19 and the site follows it: the six pages carrying
   `magmacrunchmedia@gmail.com` now read `info@magmacrunch.com`, which is what
   Apple's reviewers and players see. `store/metadata.md` names no address, only
   the support URL, so it needed no change. `jake@` is the address the
   enrollment form wants.

   One trap when testing: a message sent from the same Gmail account the alias
   forwards to is silently dropped by Gmail, which discards anything arriving
   with a Message-ID it just sent. ImprovMX works around it by rewriting the
   header and re-signing, which then fails DMARC alignment and lands in spam. So
   a self-addressed test looks like a broken forwarder and is not one. Send from
   an unrelated address instead.

3. **Then enroll**, as an organization, with the number and the work address.

## What does not wait for any of this

The app itself. Everything in this folder and in `ios/` is finished and
verified except the parts that need the account to exist: the Game Center
capability, the eight leaderboards, the fifteen achievements, and the upload.
The art for those entries is drawn and sitting in `store/game-center/`.
