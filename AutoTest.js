const fs = require("fs");
const { chromium } = require("playwright");

// URL, vary on different machines
const SERVER_URL = "http://10.151.220.244:5000";
const LOST_FILE = "lost.txt";

const WAIT_TIMEOUT = 1000 * 60 * 120;
const AFTER_END_WAIT = 3000;

function readLostTests() {
    return fs.readFileSync(LOST_FILE, "utf-8")
        .split(/\r?\n/)
        .map(line => line.trim())
        .filter(line => line.length > 0 && !line.startsWith("#"))
        .map(line => {
            const parts = line.split(/\s+/);

            if (parts.length !== 3) {
                throw new Error(`Invalid line in lost.txt: ${line}`);
            }

            return {
                videoName: parts[0],
                codec: parts[1],
                fps: parts[2]
            };
        });
}

async function waitUntilStatusDone(page) {
    await page.waitForFunction(() => {
        const status = document.querySelector("#statusText")?.innerText || "";
        return status.includes("Success") || status.includes("Failed");
    }, null, { timeout: WAIT_TIMEOUT });

    return await page.locator("#statusText").innerText();
}

async function waitUntilPlaybackStarted(page) {
    await page.waitForFunction(() => {
        const video = document.querySelector("#videoPlayer");
        return video && !video.paused && video.readyState >= 2;
    }, null, { timeout: WAIT_TIMEOUT });
}

async function waitUntilPlaybackEnded(page) {
    await page.waitForFunction(() => {
        const video = document.querySelector("#videoPlayer");
        return video && video.ended;
    }, null, { timeout: WAIT_TIMEOUT });
}

async function runOneTest(page, videoName, codec, fps) {
    console.log(`\n===== Start: ${videoName}, ${codec}, ${fps} =====`);

    await page.goto(SERVER_URL, { waitUntil: "domcontentloaded", timeout: WAIT_TIMEOUT });

    await page.fill("#videoInput", videoName);
    await page.selectOption("#codecSelect", codec);
    await page.selectOption("#fpsSelect", fps);

    await page.click("#playBtn");

    console.log("Waiting for backend result...");

    const statusText = await waitUntilStatusDone(page);

    if (statusText.includes("Failed")) {
        console.log(`Backend failed: ${videoName}, ${codec}, ${fps}`);
        console.log(statusText);
        throw new Error("Backend returned Failed");
    }

    console.log("Backend accepted, waiting for playback...");

    await waitUntilPlaybackStarted(page);
    console.log("Playback started.");

    await waitUntilPlaybackEnded(page);
    console.log("Playback ended.");

    await page.waitForTimeout(AFTER_END_WAIT);

    console.log(`===== Finished: ${videoName}, ${codec}, ${fps} =====`);
}

(async () => {
    const tests = readLostTests();

    console.log(`Loaded ${tests.length} lost tests.`);

    const browser = await chromium.launch({
        headless: false
    });

    const page = await browser.newPage();

    page.setDefaultTimeout(WAIT_TIMEOUT);
    page.setDefaultNavigationTimeout(WAIT_TIMEOUT);

    page.on("console", msg => {
        console.log("[browser]", msg.text());
    });

    for (const test of tests) {
        const { videoName, codec, fps } = test;

        try {
            await runOneTest(page, videoName, codec, fps);
        } catch (error) {
            console.log(`\nFATAL ERROR in ${videoName}, ${codec}, ${fps}`);
            console.log(error.message);
            console.log("Stop all tests. No next request will be sent.");

            await browser.close();
            process.exit(1);
        }
    }

    console.log("\nAll lost tests finished.");
    await browser.close();
})();