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
| Seller name on the App Store | The legal entity name, so `MAGMACRUNCH MEDIA LLC`. This is the whole reason for enrolling as an organization: an individual enrollment lists a personal legal name instead. |
| Website | `https://magmacrunch.com`. Apple requires it to be publicly available, functional, and on a domain associated with the organization. It is, and it now links to the game, the privacy page and the support page. |
| Binding authority | The owner. Apple requires whoever enrolls to be able to bind the company to agreements. |
| Cost | The program is $99/year. A D-U-N-S Number is free. |

## What is outstanding

1. **A D-U-N-S Number.** Look the company up first at
   `developer.apple.com/enroll/duns-lookup/`: D&B may already hold a record
   for a registered LLC. If not, the same page requests one, and asks for the
   legal entity name, headquarters address, mailing address and work contact.
   Have the PA registration documents to hand, since a D&B representative may
   call to verify. Allow up to 5 business days for the number and up to 2 more
   for Apple to see it. Paying to expedite does not shorten it.

2. **A work email address on `magmacrunch.com`.** Apple: "Your work email
   address needs to be associated with your organization's domain name." The
   domain has **no MX records today** (checked 2026-09-19; DNS is on Google
   Cloud DNS), so there is no mailbox to use. This is the piece most likely to
   be discovered late, because everything else about the company is already in
   order.

   Note the knock-on: `magmacrunchmedia@gmail.com` is the address on the
   support page and in `store/metadata.md`. Once a company address exists,
   those should change with it.

3. **Then enroll**, as an organization, with the number and the work address.

## What does not wait for any of this

The app itself. Everything in this folder and in `ios/` is finished and
verified except the parts that need the account to exist: the Game Center
capability, the eight leaderboards, the fifteen achievements, and the upload.
The art for those entries is drawn and sitting in `store/game-center/`.
