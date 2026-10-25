# BaanDee Living: Company Brief

BaanDee Living Co., Ltd. is a fictional Thai retailer of household goods. It sells online and through stores, with a central warehouse near Bangkok and regional stock points. All records and people in this class are synthetic.

After the Home Refresh campaign, support agents received more delayed-order complaints. To answer one customer, an agent may need a support export, order information, product and inventory data, fulfilment events, and the service policy. The sources do not always use the same identifiers or refresh at the same time.

## Class 1 challenge

The team is demonstrating a read-only **Delayed Order Support Copilot**. It should:

- identify the correct ticket and order when evidence permits;
- show evidence with its source and timestamp;
- apply an explicit service policy;
- draft a response that separates verified facts from uncertainty; and
- avoid unsupported delivery promises.

The MVP does not send messages, change orders, approve refunds, or provide secure production access.

## Three demonstration cases

| Ticket | Situation | Expected behavior |
|---|---|---|
| `TKT-260731-042` | Ticket uses `OD1842`; current status conflicts with the morning export | Use the approved crosswalk, show both timestamps, and withhold a new delivery date |
| `TKT-260731-099` | Order reference cannot be verified | State that the order is unverified and request human follow-up |
| `TKT-260731-117` | Morning export and current API disagree | Use the authoritative current status while preserving the older evidence |

## Your role during the demonstration

Predict what should happen, inspect the evidence, question correction rules, identify unsupported claims, and connect each tool to its job. You are not expected to install or code during this class.

