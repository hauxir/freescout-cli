# FreeScout CLI

Command-line interface for managing FreeScout helpdesk.

## Installation

```bash
pip install -e .
```

## Configuration

Configure your FreeScout connection:

```bash
freescout login
```

Or use environment variables:
- `FREESCOUT_URL` - FreeScout server URL
- `FREESCOUT_API_KEY` - API key

## Usage

### Mailboxes

```bash
# List mailboxes
freescout mailboxes

# List folders in a mailbox
freescout mailbox-folders <mailbox_id>

# List custom fields for a mailbox
freescout mailbox-fields <mailbox_id>
```

### Conversations

```bash
# List conversations
freescout conversations
freescout conversations --mailbox 1 --status active
freescout conversations --tag urgent --assigned 5

# View conversation details
freescout conversation <id>
freescout conversation <id> --threads

# Create conversation
freescout conversation-create <mailbox_id> "Subject" "customer@email.com" "Message text"

# Update conversation
freescout conversation-update <id> --by-user 1 --status closed
freescout conversation-update <id> --by-user 1 --assign-to 5

# Close conversation
freescout conversation-close <id> --by-user 1

# Delete conversation
freescout conversation-delete <id>
```

### Replies and Notes

```bash
# Reply to a conversation
freescout reply <conversation_id> "Reply message" --user 1

# Add a note
freescout note <conversation_id> "Internal note" --user 1
```

### Customers

```bash
# List customers
freescout customers
freescout customers --email "customer@example.com"

# View customer
freescout customer <id>

# Create customer
freescout customer-create "John" "Doe" --email "john@example.com"

# Update customer
freescout customer-update <id> --company "Acme Inc"
```

### Users

```bash
# List users
freescout users

# View user
freescout user <id>

# Create user
freescout user-create "John" "Doe" "john@example.com"

# Delete user
freescout user-delete <id> --by-user 1
```

### Tags

```bash
# List tags
freescout tags

# Set tags on a conversation
freescout tags-set <conversation_id> tag1 tag2 tag3
```

### Timelogs

```bash
# List timelogs for a conversation
freescout timelogs <conversation_id>
```

### Webhooks

```bash
# Create webhook
freescout webhook-create "https://example.com/hook" convo.created convo.status

# Delete webhook
freescout webhook-delete <id>
```

### Configuration

```bash
# Show current config
freescout config-show

# Clear config
freescout logout
```

## License

MIT
