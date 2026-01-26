import { Inject, Injectable } from "@nestjs/common";
import * as crypto from "crypto";

export interface AuthCorePolicy {
  minLength: number;
  requireUppercase: boolean;
  requireLowercase: boolean;
  requireDigits: boolean;
  requireSymbols: boolean;
}

export interface AuthCoreConfig {
  hashName: string;
  iterations: number;
  saltBytes: number;
  tokenBytes: number;
  tokenTtlSeconds: number;
  pepperEnv: string;
  issuer: string;
  policy: AuthCorePolicy;
}

export interface AuthCoreTokenPayload {
  iss: string;
  sub: string;
  iat: number;
  exp: number;
  aud?: string;
  scopes?: string[];
  [claim: string]: unknown;
}

export const AUTH_CORE_CONFIG = "AUTH_CORE_CONFIG";

export interface AuthCoreMetadata {
  module: string;
  issuer: string;
  hash: string;
  iterations: number;
  token_ttl_seconds: number;
  tokenTtlSeconds: number;
  pepper_env: string;
  pepperEnv: string;
  pepper_configured: boolean;
  pepperConfigured: boolean;
  [key: string]: unknown;
}

export interface AuthCoreHealthPayload {
  status: "ok" | "degraded";
  metadata: AuthCoreMetadata;
  issues: string[];
}

function base64Url(buffer: Buffer): string {
  return buffer
    .toString("base64")
    .replace(/=+$/u, "")
    .replace(/\+/gu, "-")
    .replace(/\//gu, "_");
}

function base64UrlDecode(segment: string): Buffer {
  const padLength = (4 - (segment.length % 4)) % 4;
  const padded = segment + "=".repeat(padLength);
  const normalized = padded.replace(/-/gu, "+").replace(/_/gu, "/");
  return Buffer.from(normalized, "base64");
}

@Injectable()
export class AuthCoreService {
  private pepperValue?: Buffer;

  constructor(@Inject(AUTH_CORE_CONFIG) private readonly config: AuthCoreConfig) {}

  hashPassword(password: string): string {
    if (!this.validatePassword(password)) {
      throw new Error("Password does not meet configured Auth Core policy requirements");
    }

    const salt = crypto.randomBytes(this.config.saltBytes);
    const derived = crypto.pbkdf2Sync(
      Buffer.from(password, "utf8"),
      salt,
      this.config.iterations,
      64,
      this.config.hashName,
    );

    const encoded = [
      "pbkdf2",
      this.config.hashName,
      String(this.config.iterations),
      base64Url(salt),
      base64Url(derived),
    ].join("$");
    return encoded;
  }

  verifyPassword(password: string, encoded: string): boolean {
    const segments = encoded.split("$");
    if (segments.length !== 5) {
      return false;
    }

    const [, hashName, iterationStr, saltSegment, digestSegment] = segments;
    const iterations = Number.parseInt(iterationStr, 10);
    if (!Number.isSafeInteger(iterations) || iterations <= 0) {
      return false;
    }

    const salt = base64UrlDecode(saltSegment);
    const expected = base64UrlDecode(digestSegment);

    const derived = crypto.pbkdf2Sync(
      Buffer.from(password, "utf8"),
      salt,
      iterations,
      expected.length,
      hashName,
    );

    return crypto.timingSafeEqual(expected, derived);
  }

  issueToken(
    subject: string,
    options: {
      audience?: string;
      scopes?: string[];
      ttlSeconds?: number;
      customClaims?: Record<string, unknown>;
    } = {},
  ): string {
    const issuedAt = Math.floor(Date.now() / 1000);
    const ttlSeconds = options.ttlSeconds ?? this.config.tokenTtlSeconds;

    const payload: AuthCoreTokenPayload = {
      iss: this.config.issuer,
      sub: subject,
      iat: issuedAt,
      exp: issuedAt + ttlSeconds,
    };

    if (options.audience) {
      payload.aud = options.audience;
    }

    if (options.scopes) {
      payload.scopes = [...options.scopes];
    }

    if (options.customClaims) {
      Object.assign(payload, options.customClaims);
    }

    const header = { alg: "HS256", typ: "JWT" };
    const headerSegment = base64Url(Buffer.from(JSON.stringify(header)));
    const payloadSegment = base64Url(Buffer.from(JSON.stringify(payload)));
    const signingInput = `${headerSegment}.${payloadSegment}`;
    const signature = base64Url(this.sign(Buffer.from(signingInput, "utf8")));

    return `${headerSegment}.${payloadSegment}.${signature}`;
  }

  verifyToken(token: string): AuthCoreTokenPayload {
    const segments = token.split(".");
    if (segments.length !== 3) {
      throw new Error("Auth Core token has unexpected structure");
    }

    const [headerSegment, payloadSegment, signatureSegment] = segments;
    const signingInput = `${headerSegment}.${payloadSegment}`;

    const expectedSignature = this.sign(Buffer.from(signingInput, "utf8"));
    const providedSignature = base64UrlDecode(signatureSegment);

    if (!crypto.timingSafeEqual(expectedSignature, providedSignature)) {
      throw new Error("Auth Core token signature validation failed");
    }

    const payloadBuffer = base64UrlDecode(payloadSegment);
    const payload = JSON.parse(payloadBuffer.toString("utf8")) as AuthCoreTokenPayload;

    if (payload.exp && Math.floor(Date.now() / 1000) > payload.exp) {
      throw new Error("Auth Core token has expired");
    }

    return payload;
  }

  metadata(): AuthCoreMetadata {
    const pepperConfigured = Boolean(process.env[this.config.pepperEnv]);

    return {
      module: "auth_core",
      issuer: this.config.issuer,
      hash: this.config.hashName,
      iterations: this.config.iterations,
      token_ttl_seconds: this.config.tokenTtlSeconds,
      tokenTtlSeconds: this.config.tokenTtlSeconds,
      pepper_env: this.config.pepperEnv,
      pepperEnv: this.config.pepperEnv,
      pepper_configured: pepperConfigured,
      pepperConfigured,
    };
  }

  health(): AuthCoreHealthPayload {
    const metadata = this.metadata();
    const pepperConfigured = Boolean(metadata["pepper_configured"]);
    const issues: string[] = [];

    if (!pepperConfigured) {
      issues.push("pepper_not_configured");
    }

    return {
      status: pepperConfigured ? "ok" : "degraded",
      metadata,
      issues,
    };
  }

  validatePassword(password: string): boolean {
    if (password.length < this.config.policy.minLength) {
      return false;
    }
    const checks: Array<[boolean, boolean]> = [
      [this.config.policy.requireUppercase, /[A-Z]/u.test(password)],
      [this.config.policy.requireLowercase, /[a-z]/u.test(password)],
      [this.config.policy.requireDigits, /[0-9]/u.test(password)],
      [this.config.policy.requireSymbols, /[^A-Za-z0-9]/u.test(password)],
    ];

    return checks.every(([required, result]) => !required || result);
  }

  private sign(message: Buffer): Buffer {
    return crypto.createHmac("sha256", this.pepper()).update(message).digest();
  }

  private pepper(): Buffer {
    if (this.pepperValue) {
      return this.pepperValue;
    }

    const secret = process.env[this.config.pepperEnv];
    if (secret) {
      this.pepperValue = Buffer.from(secret, "utf8");
      return this.pepperValue;
    }

    this.pepperValue = crypto.randomBytes(32);
    return this.pepperValue;
  }
}
