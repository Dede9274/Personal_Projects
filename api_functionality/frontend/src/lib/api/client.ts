const API_BASE_URL = (
  typeof window === "undefined"
    ? process.env.INTERNAL_API_URL ??
      process.env.NEXT_PUBLIC_API_URL ??
      "http://localhost:8000"
    : process.env.NEXT_PUBLIC_API_URL ??
      "http://localhost:8000"
).replace(/\/$/, "");

type FastApiValidationError = {
  msg?: string;
};

type FastApiErrorBody = {
  detail?: string | FastApiValidationError[];
};

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function getErrorMessage(body: FastApiErrorBody | null, status: number): string {
  if (typeof body?.detail === "string") {
    return body.detail;
  }

  if (Array.isArray(body?.detail)) {
    const messages = body.detail
      .map((error) => error.msg)
      .filter((message): message is string => Boolean(message));

    if (messages.length > 0) {
      return messages.join(", ");
    }
  }

  return `API request failed with status ${status}`;
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as FastApiErrorBody | null;
    throw new ApiError(getErrorMessage(body, response.status), response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
