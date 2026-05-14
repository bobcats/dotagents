import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { resolveArtifactConfig, resolveS3ClientConfig } from "./config.js";

describe("resolveArtifactConfig", () => {
	it("uses Buildr production defaults", () => {
		assert.deepEqual(resolveArtifactConfig({}), {
			baseUrl: "https://artifacts.buildrtools.com",
			bucketName: "buildr-bizops-artifacts",
		});
	});

	it("respects explicit bucket and base URL", () => {
		assert.deepEqual(
			resolveArtifactConfig({
				ARTIFACTS_BASE_URL: "https://cdn.example.test/",
				ARTIFACTS_S3_BUCKET: "custom-bucket",
			}),
			{ baseUrl: "https://cdn.example.test", bucketName: "custom-bucket" },
		);
	});
});

describe("resolveS3ClientConfig", () => {
	it("defaults forcePathStyle on when an endpoint is configured", () => {
		assert.deepEqual(resolveS3ClientConfig({ ARTIFACTS_S3_ENDPOINT: "http://127.0.0.1:4568" }), {
			endpoint: "http://127.0.0.1:4568",
			forcePathStyle: true,
			region: undefined,
		});
	});

	it("lets ARTIFACTS_S3_FORCE_PATH_STYLE override endpoint default", () => {
		assert.deepEqual(
			resolveS3ClientConfig({
				ARTIFACTS_S3_ENDPOINT: "http://127.0.0.1:4568",
				ARTIFACTS_S3_FORCE_PATH_STYLE: "false",
				AWS_REGION: "us-west-2",
			}),
			{ endpoint: "http://127.0.0.1:4568", forcePathStyle: false, region: "us-west-2" },
		);
	});
});
