from typing import Any

import httpx


class FreeScoutClient:
    def __init__(self, base_url: str, api_key: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client = httpx.Client(timeout=30.0)

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-FreeScout-API-Key"] = self.api_key
        return headers

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        response = self._client.get(f"{self.base_url}{path}", headers=self._headers(), params=params)
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]

    def _post(self, path: str, data: dict[str, Any] | None = None) -> httpx.Response:
        response = self._client.post(f"{self.base_url}{path}", json=data or {}, headers=self._headers())
        response.raise_for_status()
        return response

    def _put(self, path: str, data: dict[str, Any]) -> httpx.Response:
        response = self._client.put(f"{self.base_url}{path}", json=data, headers=self._headers())
        response.raise_for_status()
        return response

    def _delete(self, path: str, params: dict[str, Any] | None = None) -> httpx.Response:
        response = self._client.delete(f"{self.base_url}{path}", headers=self._headers(), params=params)
        response.raise_for_status()
        return response

    # === Conversations ===

    def get_conversations(
        self,
        mailbox_id: int | None = None,
        folder_id: int | None = None,
        status: str | None = None,
        assigned_to: int | None = None,
        customer_email: str | None = None,
        customer_id: int | None = None,
        tag: str | None = None,
        page: int = 1,
        page_size: int = 50,
        embed: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"page": page, "pageSize": page_size}
        if mailbox_id:
            params["mailboxId"] = mailbox_id
        if folder_id:
            params["folderId"] = folder_id
        if status:
            params["status"] = status
        if assigned_to:
            params["assignedTo"] = assigned_to
        if customer_email:
            params["customerEmail"] = customer_email
        if customer_id:
            params["customerId"] = customer_id
        if tag:
            params["tag"] = tag
        if embed:
            params["embed"] = embed
        return self._get("/api/conversations", params)

    def get_conversation(self, conversation_id: int, embed: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if embed:
            params["embed"] = embed
        return self._get(f"/api/conversations/{conversation_id}", params)

    def create_conversation(
        self,
        mailbox_id: int,
        subject: str,
        customer_email: str,
        thread_text: str,
        conv_type: str = "email",
        status: str = "active",
        assign_to: int | None = None,
        imported: bool = False,
    ) -> int:
        data: dict[str, Any] = {
            "type": conv_type,
            "mailboxId": mailbox_id,
            "subject": subject,
            "customer": {"email": customer_email},
            "threads": [{"type": "customer", "text": thread_text}],
            "status": status,
            "imported": imported,
        }
        if assign_to:
            data["assignTo"] = assign_to
        response = self._post("/api/conversations", data)
        resource_id = response.headers.get("Resource-ID")
        return int(resource_id) if resource_id else 0

    def update_conversation(
        self,
        conversation_id: int,
        by_user: int,
        status: str | None = None,
        assign_to: int | None = None,
        mailbox_id: int | None = None,
        customer_id: int | None = None,
        subject: str | None = None,
    ) -> None:
        data: dict[str, Any] = {"byUser": by_user}
        if status:
            data["status"] = status
        if assign_to is not None:
            data["assignTo"] = assign_to
        if mailbox_id:
            data["mailboxId"] = mailbox_id
        if customer_id:
            data["customerId"] = customer_id
        if subject:
            data["subject"] = subject
        self._put(f"/api/conversations/{conversation_id}", data)

    def delete_conversation(self, conversation_id: int) -> None:
        self._delete(f"/api/conversations/{conversation_id}")

    # === Threads ===

    def create_thread(
        self,
        conversation_id: int,
        thread_type: str,
        text: str,
        user: int | None = None,
        customer_email: str | None = None,
        status: str | None = None,
        to: list[str] | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
    ) -> int:
        data: dict[str, Any] = {"type": thread_type, "text": text}
        if user:
            data["user"] = user
        if customer_email:
            data["customer"] = {"email": customer_email}
        if status:
            data["status"] = status
        if to:
            data["to"] = to
        if cc:
            data["cc"] = cc
        if bcc:
            data["bcc"] = bcc
        response = self._post(f"/api/conversations/{conversation_id}/threads", data)
        resource_id = response.headers.get("Resource-ID")
        return int(resource_id) if resource_id else 0

    # === Customers ===

    def get_customers(
        self,
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"page": page, "pageSize": page_size}
        if first_name:
            params["firstName"] = first_name
        if last_name:
            params["lastName"] = last_name
        if email:
            params["email"] = email
        if phone:
            params["phone"] = phone
        return self._get("/api/customers", params)

    def get_customer(self, customer_id: int) -> dict[str, Any]:
        return self._get(f"/api/customers/{customer_id}")

    def create_customer(
        self,
        first_name: str,
        last_name: str,
        email: str | None = None,
        phone: str | None = None,
        job_title: str | None = None,
        company: str | None = None,
        notes: str | None = None,
    ) -> int:
        data: dict[str, Any] = {"firstName": first_name, "lastName": last_name}
        if email:
            data["emails"] = [{"value": email}]
        if phone:
            data["phones"] = [{"value": phone}]
        if job_title:
            data["jobTitle"] = job_title
        if company:
            data["company"] = company
        if notes:
            data["notes"] = notes
        response = self._post("/api/customers", data)
        resource_id = response.headers.get("Resource-ID")
        return int(resource_id) if resource_id else 0

    def update_customer(
        self,
        customer_id: int,
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        job_title: str | None = None,
        company: str | None = None,
        notes: str | None = None,
    ) -> None:
        data: dict[str, Any] = {}
        if first_name:
            data["firstName"] = first_name
        if last_name:
            data["lastName"] = last_name
        if email:
            data["emails"] = [{"value": email}]
        if phone:
            data["phones"] = [{"value": phone}]
        if job_title:
            data["jobTitle"] = job_title
        if company:
            data["company"] = company
        if notes:
            data["notes"] = notes
        self._put(f"/api/customers/{customer_id}", data)

    # === Mailboxes ===

    def get_mailboxes(self, user_id: int | None = None, page: int = 1, page_size: int = 50) -> dict[str, Any]:
        params: dict[str, Any] = {"page": page, "pageSize": page_size}
        if user_id:
            params["userId"] = user_id
        return self._get("/api/mailboxes", params)

    def get_mailbox_folders(
        self, mailbox_id: int, user_id: int | None = None, page_size: int = 50
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"pageSize": page_size}
        if user_id:
            params["userId"] = user_id
        return self._get(f"/api/mailboxes/{mailbox_id}/folders", params)

    def get_mailbox_custom_fields(self, mailbox_id: int) -> dict[str, Any]:
        return self._get(f"/api/mailboxes/{mailbox_id}/custom_fields")

    # === Users ===

    def get_users(self, email: str | None = None, page: int = 1, page_size: int = 50) -> dict[str, Any]:
        params: dict[str, Any] = {"page": page, "pageSize": page_size}
        if email:
            params["email"] = email
        return self._get("/api/users", params)

    def get_user(self, user_id: int) -> dict[str, Any]:
        return self._get(f"/api/users/{user_id}")

    def create_user(
        self,
        first_name: str,
        last_name: str,
        email: str,
        password: str | None = None,
        job_title: str | None = None,
        phone: str | None = None,
        timezone: str | None = None,
    ) -> int:
        data: dict[str, Any] = {"firstName": first_name, "lastName": last_name, "email": email}
        if password:
            data["password"] = password
        if job_title:
            data["jobTitle"] = job_title
        if phone:
            data["phone"] = phone
        if timezone:
            data["timezone"] = timezone
        response = self._post("/api/users", data)
        resource_id = response.headers.get("Resource-ID")
        return int(resource_id) if resource_id else 0

    def delete_user(self, user_id: int, by_user_id: int, assign_to: dict[str, int] | None = None) -> None:
        params: dict[str, Any] = {"byUserId": by_user_id}
        if assign_to:
            params["assignTo"] = assign_to
        self._delete(f"/api/users/{user_id}", params)

    # === Tags ===

    def get_tags(self, conversation_id: int | None = None, page: int = 1, page_size: int = 50) -> dict[str, Any]:
        params: dict[str, Any] = {"page": page, "pageSize": page_size}
        if conversation_id:
            params["conversationId"] = conversation_id
        return self._get("/api/tags", params)

    def update_conversation_tags(self, conversation_id: int, tags: list[str]) -> None:
        self._put(f"/api/conversations/{conversation_id}/tags", {"tags": tags})

    # === Custom Fields ===

    def update_conversation_custom_fields(
        self, conversation_id: int, custom_fields: list[dict[str, Any]]
    ) -> None:
        self._put(f"/api/conversations/{conversation_id}/custom_fields", {"customFields": custom_fields})

    def update_customer_fields(self, customer_id: int, customer_fields: list[dict[str, Any]]) -> None:
        self._put(f"/api/customers/{customer_id}/customer_fields", {"customerFields": customer_fields})

    # === Timelogs ===

    def get_timelogs(self, conversation_id: int, page: int = 1, page_size: int = 50) -> dict[str, Any]:
        params: dict[str, Any] = {"page": page, "pageSize": page_size}
        return self._get(f"/api/conversations/{conversation_id}/timelogs", params)

    # === Webhooks ===

    def create_webhook(self, url: str, events: list[str]) -> int:
        response = self._post("/api/webhooks", {"url": url, "events": events})
        resource_id = response.headers.get("Resource-ID")
        return int(resource_id) if resource_id else 0

    def delete_webhook(self, webhook_id: int) -> None:
        self._delete(f"/api/webhooks/{webhook_id}")

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "FreeScoutClient":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()
