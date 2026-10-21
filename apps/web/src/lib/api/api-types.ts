import type { paths } from "@/lib/api/api-schema";

type HttpMethod = "get" | "post" | "put" | "patch" | "delete";

type Operation<
  P extends keyof paths,
  M extends HttpMethod,
> = M extends keyof paths[P] ? paths[P][M] : never;

type JsonResponse<Op> =
  Op extends { responses: infer Responses }
    ? {
        [Status in keyof Responses]:
          Responses[Status] extends {
            content: { "application/json": infer Body };
          }
            ? Body
            : never;
      }[keyof Responses]
    : never;

export type ApiResponse<
  P extends keyof paths,
  M extends HttpMethod,
> = JsonResponse<Operation<P, M>>;