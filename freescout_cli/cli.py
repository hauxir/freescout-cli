import os
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from freescout_cli import config
from freescout_cli.client import FreeScoutClient

console = Console()


def get_client() -> FreeScoutClient:
    base_url = os.environ.get("FREESCOUT_URL") or config.get_url()
    if not base_url:
        console.print("[red]Error: No FreeScout URL configured. Run 'freescout login' first.[/red]")
        raise SystemExit(1)
    api_key = os.environ.get("FREESCOUT_API_KEY") or config.get_api_key()
    return FreeScoutClient(base_url, api_key)


@click.group()
def main() -> None:
    """FreeScout CLI - Manage your FreeScout helpdesk from the command line."""


# === Configuration ===


@main.command()
@click.option("--url", "-u", help="FreeScout server URL")
@click.option("--api-key", "-k", help="API key")
def login(url: str | None, api_key: str | None) -> None:
    """Configure FreeScout connection."""
    if not url:
        current_url = config.get_url()
        if current_url:
            url = click.prompt("FreeScout URL", default=current_url)
        else:
            url = click.prompt("FreeScout URL (e.g. https://helpdesk.example.com)")
    config.set_url(url)

    if not api_key:
        api_key = click.prompt("API Key", hide_input=True)
    config.set_api_key(api_key)

    console.print("[green]Configuration saved![/green]")
    console.print(f"Config file: {config.CONFIG_FILE}")


@main.command()
def logout() -> None:
    """Clear saved configuration."""
    config.clear_config()
    console.print("[green]Logged out - configuration cleared[/green]")


@main.command("config-show")
def config_show() -> None:
    """Show current configuration."""
    console.print(f"[bold]Config file:[/bold] {config.CONFIG_FILE}")
    url = config.get_url()
    console.print(f"[bold]URL:[/bold] {url or '[dim]not set[/dim]'}")
    api_key = config.get_api_key()
    if api_key:
        console.print(f"[bold]API Key:[/bold] {api_key[:10]}...")
    else:
        console.print("[bold]API Key:[/bold] [dim]not set[/dim]")


# === Mailboxes ===


@main.command()
def mailboxes() -> None:
    """List all mailboxes."""
    with get_client() as client:
        data = client.get_mailboxes()
        items: list[dict[str, Any]] = data.get("_embedded", {}).get("mailboxes", [])
        table = Table(title="Mailboxes")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Email", style="dim")
        for mailbox in items:
            table.add_row(str(mailbox.get("id")), str(mailbox.get("name")), str(mailbox.get("email", "")))
        console.print(table)


@main.command("mailbox-folders")
@click.argument("mailbox_id", type=int)
def mailbox_folders(mailbox_id: int) -> None:
    """List folders in a mailbox."""
    with get_client() as client:
        data = client.get_mailbox_folders(mailbox_id)
        items: list[dict[str, Any]] = data.get("_embedded", {}).get("folders", [])
        table = Table(title=f"Folders (Mailbox {mailbox_id})")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Type", style="dim")
        table.add_column("Active", style="dim")
        table.add_column("Total", style="dim")
        for folder in items:
            table.add_row(
                str(folder.get("id")),
                str(folder.get("name")),
                str(folder.get("type", "")),
                str(folder.get("activeCount", 0)),
                str(folder.get("totalCount", 0)),
            )
        console.print(table)


@main.command("mailbox-fields")
@click.argument("mailbox_id", type=int)
def mailbox_fields(mailbox_id: int) -> None:
    """List custom fields for a mailbox."""
    with get_client() as client:
        data = client.get_mailbox_custom_fields(mailbox_id)
        items: list[dict[str, Any]] = data.get("_embedded", {}).get("custom_fields", [])
        if not items:
            console.print("[dim]No custom fields defined[/dim]")
            return
        table = Table(title=f"Custom Fields (Mailbox {mailbox_id})")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Type", style="dim")
        table.add_column("Required", style="dim")
        for field in items:
            table.add_row(
                str(field.get("id")),
                str(field.get("name")),
                str(field.get("type", "")),
                "Yes" if field.get("required") else "No",
            )
        console.print(table)


# === Conversations ===


@main.command()
@click.option("--mailbox", "-m", type=int, help="Filter by mailbox ID")
@click.option("--folder", "-f", type=int, help="Filter by folder ID")
@click.option("--status", "-s", type=click.Choice(["active", "pending", "closed", "spam"]), help="Filter by status")
@click.option("--assigned", "-a", type=int, help="Filter by assigned user ID")
@click.option("--tag", "-t", help="Filter by tag")
@click.option("--customer-email", "-e", help="Filter by customer email")
@click.option("--page", "-p", default=1, help="Page number")
@click.option("--limit", "-l", default=25, help="Results per page")
def conversations(
    mailbox: int | None,
    folder: int | None,
    status: str | None,
    assigned: int | None,
    tag: str | None,
    customer_email: str | None,
    page: int,
    limit: int,
) -> None:
    """List conversations."""
    with get_client() as client:
        data = client.get_conversations(
            mailbox_id=mailbox,
            folder_id=folder,
            status=status,
            assigned_to=assigned,
            tag=tag,
            customer_email=customer_email,
            page=page,
            page_size=limit,
        )
        items: list[dict[str, Any]] = data.get("_embedded", {}).get("conversations", [])
        if not items:
            console.print("[dim]No conversations found[/dim]")
            return
        table = Table(title="Conversations")
        table.add_column("ID", style="cyan")
        table.add_column("Number", style="dim")
        table.add_column("Subject", style="green", max_width=40)
        table.add_column("Status", style="yellow")
        table.add_column("Customer", style="dim", max_width=25)
        for conv in items:
            customer: dict[str, Any] = conv.get("customer", {})
            customer_name = f"{customer.get('firstName', '')} {customer.get('lastName', '')}".strip() or customer.get(
                "email", ""
            )
            table.add_row(
                str(conv.get("id")),
                str(conv.get("number", "")),
                str(conv.get("subject", "")[:40]),
                str(conv.get("status", "")),
                str(customer_name)[:25],
            )
        console.print(table)

        # Show pagination info
        page_info = data.get("page", {})
        if page_info:
            console.print(
                f"\n[dim]Page {page_info.get('number', page)} of {page_info.get('totalPages', 1)} "
                f"({page_info.get('totalElements', 0)} total)[/dim]"
            )


@main.command("conversation")
@click.argument("conversation_id", type=int)
@click.option("--threads", "-t", is_flag=True, help="Include threads")
def conversation(conversation_id: int, threads: bool) -> None:
    """Show conversation details."""
    with get_client() as client:
        embed = "threads" if threads else None
        data = client.get_conversation(conversation_id, embed=embed)

        console.print(f"[bold cyan]Conversation #{data.get('number')}[/bold cyan]")
        console.print(f"[bold]Subject:[/bold] {data.get('subject')}")
        console.print(f"[bold]Status:[/bold] {data.get('status')}")
        console.print(f"[bold]Type:[/bold] {data.get('type')}")
        console.print(f"[bold]Mailbox ID:[/bold] {data.get('mailboxId')}")

        customer: dict[str, Any] = data.get("customer", {})
        customer_name = f"{customer.get('firstName', '')} {customer.get('lastName', '')}".strip()
        console.print(f"[bold]Customer:[/bold] {customer_name} ({customer.get('email', '')})")

        assignee = data.get("assignee")
        if assignee:
            console.print(f"[bold]Assigned to:[/bold] {assignee.get('firstName', '')} {assignee.get('lastName', '')}")

        tags: list[dict[str, Any]] = data.get("tags", [])
        if tags:
            tag_names = [str(t.get("name", "")) for t in tags]
            console.print(f"[bold]Tags:[/bold] {', '.join(tag_names)}")

        console.print(f"[bold]Created:[/bold] {data.get('createdAt')}")

        # Show threads if requested
        embedded: dict[str, Any] = data.get("_embedded", {})
        thread_list: list[dict[str, Any]] = embedded.get("threads", [])
        if thread_list:
            console.print(f"\n[bold]Threads ({len(thread_list)}):[/bold]")
            for thread in thread_list:
                thread_type = thread.get("type", "")
                created_by = thread.get("createdBy", {})
                author = f"{created_by.get('firstName', '')} {created_by.get('lastName', '')}".strip()
                console.print(f"\n[dim]{thread.get('createdAt')}[/dim] [{thread_type}] by {author or 'Customer'}")
                body = thread.get("body", "")
                if body:
                    # Strip HTML tags for display
                    import re

                    clean_body = re.sub(r"<[^>]+>", "", body)
                    console.print(clean_body[:500])


@main.command("conversation-create")
@click.argument("mailbox_id", type=int)
@click.argument("subject")
@click.argument("customer_email")
@click.argument("message")
@click.option("--assign-to", "-a", type=int, help="Assign to user ID")
@click.option("--status", "-s", default="active", type=click.Choice(["active", "pending", "closed"]))
def conversation_create(
    mailbox_id: int, subject: str, customer_email: str, message: str, assign_to: int | None, status: str
) -> None:
    """Create a new conversation."""
    with get_client() as client:
        conv_id = client.create_conversation(
            mailbox_id=mailbox_id,
            subject=subject,
            customer_email=customer_email,
            thread_text=message,
            status=status,
            assign_to=assign_to,
        )
        console.print(f"[green]Created conversation[/green] (ID: {conv_id})")


@main.command("conversation-update")
@click.argument("conversation_id", type=int)
@click.option("--by-user", "-b", type=int, required=True, help="User ID making the change")
@click.option("--status", "-s", type=click.Choice(["active", "pending", "closed", "spam"]), help="New status")
@click.option("--assign-to", "-a", type=int, help="Assign to user ID (0 to unassign)")
@click.option("--subject", help="New subject")
def conversation_update(
    conversation_id: int,
    by_user: int,
    status: str | None,
    assign_to: int | None,
    subject: str | None,
) -> None:
    """Update a conversation."""
    with get_client() as client:
        client.update_conversation(
            conversation_id=conversation_id,
            by_user=by_user,
            status=status,
            assign_to=assign_to,
            subject=subject,
        )
        console.print(f"[green]Updated conversation {conversation_id}[/green]")


@main.command("conversation-close")
@click.argument("conversation_id", type=int)
@click.option("--by-user", "-b", type=int, required=True, help="User ID making the change")
def conversation_close(conversation_id: int, by_user: int) -> None:
    """Close a conversation."""
    with get_client() as client:
        client.update_conversation(conversation_id=conversation_id, by_user=by_user, status="closed")
        console.print(f"[green]Closed conversation {conversation_id}[/green]")


@main.command("conversation-delete")
@click.argument("conversation_id", type=int)
@click.confirmation_option(prompt="Are you sure you want to delete this conversation?")
def conversation_delete(conversation_id: int) -> None:
    """Delete a conversation."""
    with get_client() as client:
        client.delete_conversation(conversation_id)
        console.print("[green]Conversation deleted[/green]")


# === Threads (Replies/Notes) ===


@main.command("reply")
@click.argument("conversation_id", type=int)
@click.argument("message")
@click.option("--user", "-u", type=int, required=True, help="User ID sending the reply")
@click.option("--type", "-t", "thread_type", default="message", type=click.Choice(["message", "note", "customer"]))
@click.option("--status", "-s", type=click.Choice(["active", "pending", "closed"]), help="Set conversation status")
def reply(conversation_id: int, message: str, user: int, thread_type: str, status: str | None) -> None:
    """Reply to a conversation or add a note."""
    with get_client() as client:
        thread_id = client.create_thread(
            conversation_id=conversation_id,
            thread_type=thread_type,
            text=message,
            user=user,
            status=status,
        )
        console.print(f"[green]Added {thread_type}[/green] (Thread ID: {thread_id})")


@main.command("note")
@click.argument("conversation_id", type=int)
@click.argument("message")
@click.option("--user", "-u", type=int, required=True, help="User ID adding the note")
def note(conversation_id: int, message: str, user: int) -> None:
    """Add a note to a conversation."""
    with get_client() as client:
        thread_id = client.create_thread(
            conversation_id=conversation_id,
            thread_type="note",
            text=message,
            user=user,
        )
        console.print(f"[green]Added note[/green] (Thread ID: {thread_id})")


# === Customers ===


@main.command()
@click.option("--email", "-e", help="Filter by email")
@click.option("--first-name", "-f", help="Filter by first name")
@click.option("--last-name", "-l", help="Filter by last name")
@click.option("--phone", "-p", help="Filter by phone")
@click.option("--page", default=1, help="Page number")
@click.option("--limit", default=25, help="Results per page")
def customers(
    email: str | None,
    first_name: str | None,
    last_name: str | None,
    phone: str | None,
    page: int,
    limit: int,
) -> None:
    """List customers."""
    with get_client() as client:
        data = client.get_customers(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            page=page,
            page_size=limit,
        )
        items: list[dict[str, Any]] = data.get("_embedded", {}).get("customers", [])
        if not items:
            console.print("[dim]No customers found[/dim]")
            return
        table = Table(title="Customers")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Email", style="dim")
        table.add_column("Company", style="dim")
        for cust in items:
            name = f"{cust.get('firstName', '')} {cust.get('lastName', '')}".strip()
            emails: list[dict[str, Any]] = cust.get("emails", [])
            email_str = emails[0].get("value", "") if emails else ""
            table.add_row(str(cust.get("id")), name, email_str, str(cust.get("company", "")))
        console.print(table)


@main.command("customer")
@click.argument("customer_id", type=int)
def customer(customer_id: int) -> None:
    """Show customer details."""
    with get_client() as client:
        data = client.get_customer(customer_id)
        console.print(f"[bold cyan]Customer #{data.get('id')}[/bold cyan]")
        console.print(f"[bold]Name:[/bold] {data.get('firstName', '')} {data.get('lastName', '')}")

        emails: list[dict[str, Any]] = data.get("emails", [])
        if emails:
            email_strs = [str(e.get("value", "")) for e in emails]
            console.print(f"[bold]Emails:[/bold] {', '.join(email_strs)}")

        phones: list[dict[str, Any]] = data.get("phones", [])
        if phones:
            phone_strs = [str(p.get("value", "")) for p in phones]
            console.print(f"[bold]Phones:[/bold] {', '.join(phone_strs)}")

        if data.get("company"):
            console.print(f"[bold]Company:[/bold] {data.get('company')}")
        if data.get("jobTitle"):
            console.print(f"[bold]Job Title:[/bold] {data.get('jobTitle')}")
        if data.get("notes"):
            console.print(f"[bold]Notes:[/bold] {data.get('notes')}")

        console.print(f"[bold]Created:[/bold] {data.get('createdAt')}")


@main.command("customer-create")
@click.argument("first_name")
@click.argument("last_name")
@click.option("--email", "-e", help="Email address")
@click.option("--phone", "-p", help="Phone number")
@click.option("--company", "-c", help="Company name")
@click.option("--job-title", "-j", help="Job title")
@click.option("--notes", "-n", help="Notes")
def customer_create(
    first_name: str,
    last_name: str,
    email: str | None,
    phone: str | None,
    company: str | None,
    job_title: str | None,
    notes: str | None,
) -> None:
    """Create a new customer."""
    with get_client() as client:
        customer_id = client.create_customer(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            company=company,
            job_title=job_title,
            notes=notes,
        )
        console.print(f"[green]Created customer[/green] (ID: {customer_id})")


@main.command("customer-update")
@click.argument("customer_id", type=int)
@click.option("--first-name", "-f", help="First name")
@click.option("--last-name", "-l", help="Last name")
@click.option("--email", "-e", help="Email address")
@click.option("--phone", "-p", help="Phone number")
@click.option("--company", "-c", help="Company name")
@click.option("--job-title", "-j", help="Job title")
@click.option("--notes", "-n", help="Notes")
def customer_update(
    customer_id: int,
    first_name: str | None,
    last_name: str | None,
    email: str | None,
    phone: str | None,
    company: str | None,
    job_title: str | None,
    notes: str | None,
) -> None:
    """Update a customer."""
    with get_client() as client:
        client.update_customer(
            customer_id=customer_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            company=company,
            job_title=job_title,
            notes=notes,
        )
        console.print(f"[green]Updated customer {customer_id}[/green]")


# === Users ===


@main.command()
@click.option("--email", "-e", help="Filter by email")
@click.option("--page", default=1, help="Page number")
@click.option("--limit", default=25, help="Results per page")
def users(email: str | None, page: int, limit: int) -> None:
    """List users."""
    with get_client() as client:
        data = client.get_users(email=email, page=page, page_size=limit)
        items: list[dict[str, Any]] = data.get("_embedded", {}).get("users", [])
        if not items:
            console.print("[dim]No users found[/dim]")
            return
        table = Table(title="Users")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Email", style="dim")
        table.add_column("Role", style="dim")
        for usr in items:
            name = f"{usr.get('firstName', '')} {usr.get('lastName', '')}".strip()
            table.add_row(str(usr.get("id")), name, str(usr.get("email", "")), str(usr.get("role", "")))
        console.print(table)


@main.command("user")
@click.argument("user_id", type=int)
def user(user_id: int) -> None:
    """Show user details."""
    with get_client() as client:
        data = client.get_user(user_id)
        console.print(f"[bold cyan]User #{data.get('id')}[/bold cyan]")
        console.print(f"[bold]Name:[/bold] {data.get('firstName', '')} {data.get('lastName', '')}")
        console.print(f"[bold]Email:[/bold] {data.get('email')}")
        if data.get("role"):
            console.print(f"[bold]Role:[/bold] {data.get('role')}")
        if data.get("jobTitle"):
            console.print(f"[bold]Job Title:[/bold] {data.get('jobTitle')}")
        if data.get("phone"):
            console.print(f"[bold]Phone:[/bold] {data.get('phone')}")
        if data.get("timezone"):
            console.print(f"[bold]Timezone:[/bold] {data.get('timezone')}")
        console.print(f"[bold]Created:[/bold] {data.get('createdAt')}")


@main.command("user-create")
@click.argument("first_name")
@click.argument("last_name")
@click.argument("email")
@click.option("--password", "-p", help="Password (prompted if not provided)")
@click.option("--job-title", "-j", help="Job title")
@click.option("--phone", help="Phone number")
@click.option("--timezone", "-t", help="Timezone")
def user_create(
    first_name: str,
    last_name: str,
    email: str,
    password: str | None,
    job_title: str | None,
    phone: str | None,
    timezone: str | None,
) -> None:
    """Create a new user."""
    if not password:
        password = click.prompt("Password", hide_input=True, confirmation_prompt=True)
    with get_client() as client:
        user_id = client.create_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            job_title=job_title,
            phone=phone,
            timezone=timezone,
        )
        console.print(f"[green]Created user[/green] (ID: {user_id})")


@main.command("user-delete")
@click.argument("user_id", type=int)
@click.option("--by-user", "-b", type=int, required=True, help="User ID performing the deletion")
@click.confirmation_option(prompt="Are you sure you want to delete this user?")
def user_delete(user_id: int, by_user: int) -> None:
    """Delete a user."""
    with get_client() as client:
        client.delete_user(user_id, by_user_id=by_user)
        console.print("[green]User deleted[/green]")


# === Tags ===


@main.command()
@click.option("--conversation", "-c", type=int, help="Filter by conversation ID")
@click.option("--page", default=1, help="Page number")
@click.option("--limit", default=50, help="Results per page")
def tags(conversation: int | None, page: int, limit: int) -> None:
    """List tags."""
    with get_client() as client:
        data = client.get_tags(conversation_id=conversation, page=page, page_size=limit)
        items: list[dict[str, Any]] = data.get("_embedded", {}).get("tags", [])
        if not items:
            console.print("[dim]No tags found[/dim]")
            return
        table = Table(title="Tags")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Color", style="dim")
        for tag in items:
            table.add_row(str(tag.get("id")), str(tag.get("name")), str(tag.get("color", "")))
        console.print(table)


@main.command("tags-set")
@click.argument("conversation_id", type=int)
@click.argument("tags", nargs=-1, required=True)
def tags_set(conversation_id: int, tags: tuple[str, ...]) -> None:
    """Set tags on a conversation (replaces existing tags)."""
    with get_client() as client:
        client.update_conversation_tags(conversation_id, list(tags))
        console.print(f"[green]Set tags on conversation {conversation_id}:[/green] {', '.join(tags)}")


# === Timelogs ===


@main.command("timelogs")
@click.argument("conversation_id", type=int)
@click.option("--page", default=1, help="Page number")
@click.option("--limit", default=25, help="Results per page")
def timelogs(conversation_id: int, page: int, limit: int) -> None:
    """List timelogs for a conversation."""
    with get_client() as client:
        data = client.get_timelogs(conversation_id, page=page, page_size=limit)
        items: list[dict[str, Any]] = data.get("_embedded", {}).get("timelogs", [])
        if not items:
            console.print("[dim]No timelogs found[/dim]")
            return
        table = Table(title=f"Timelogs (Conversation {conversation_id})")
        table.add_column("ID", style="cyan")
        table.add_column("User", style="green")
        table.add_column("Time (sec)", style="dim")
        table.add_column("Paused", style="dim")
        table.add_column("Created", style="dim")
        for log in items:
            usr: dict[str, Any] = log.get("user", {})
            user_name = f"{usr.get('firstName', '')} {usr.get('lastName', '')}".strip()
            table.add_row(
                str(log.get("id")),
                user_name,
                str(log.get("timeSpent", 0)),
                "Yes" if log.get("paused") else "No",
                str(log.get("createdAt", ""))[:19],
            )
        console.print(table)


# === Webhooks ===


@main.command("webhook-create")
@click.argument("url")
@click.argument("events", nargs=-1, required=True)
def webhook_create(url: str, events: tuple[str, ...]) -> None:
    """Create a webhook.

    Events: convo.assigned, convo.created, convo.deleted, convo.moved,
    convo.status, convo.customer.reply.created, convo.agent.reply.created,
    convo.note.created, customer.created, customer.updated
    """
    with get_client() as client:
        webhook_id = client.create_webhook(url, list(events))
        console.print(f"[green]Created webhook[/green] (ID: {webhook_id})")


@main.command("webhook-delete")
@click.argument("webhook_id", type=int)
@click.confirmation_option(prompt="Are you sure you want to delete this webhook?")
def webhook_delete(webhook_id: int) -> None:
    """Delete a webhook."""
    with get_client() as client:
        client.delete_webhook(webhook_id)
        console.print("[green]Webhook deleted[/green]")


if __name__ == "__main__":
    main()
