const fs = require("fs");
const { chromium } = require("playwright");

// URL
const SERVER_URL = "http://127.0.0.1:5000";
const VIDEO_FILE = "videos.txt";

const codecs = ["libx264", "libx265", "libvpx-vp9"];
const fpsList = ["24", "30", "60"];

const videos = fs.readFileSync(VIDEO_FILE, "utf-8")
    .split(/\r?\n/)
    .map(line => line.trim())
    .filter(line => line.length > 0 && !line.startsWith("#"));

async function runOneTest(page, videoName, codec, fps) {
    console.log(`\n===== Start: ${videoName}, ${codec}, ${fps} =====`);

    await page.fill("#videoInput", videoName);
    await page.selectOption("#codecSelect", codec);
    await page.selectOption("#fpsSelect", fps);

    await page.click("#playBtn");

    // 等待后端返回成功提示
    await page.waitForFunction(() => {
        const status = document.querySelector("#statusText")?.innerText || "";
        return status.includes("Success") || status.includes("Failed");
    }, { timeout: 180000 });

    const statusText = await page.locator("#statusText").innerText();

    if (statusText.includes("Failed")) {
        console.log(`Failed: ${videoName}, ${codec}, ${fps}`);
        console.log(statusText);
        return;
    }

    console.log("Backend accepted, waiting for playback...");

    // 等待视频真正开始播放
    await page.waitForFunction(() => {
        const video = document.querySelector("#videoPlayer");
        return video && !video.paused && video.readyState >= 2;
    }, { timeout: 180000 });

    console.log("Playback started.");

    // 等待视频播放结束
    await page.waitForFunction(() => {
        const video = document.querySelector("#videoPlayer");
        return video && video.ended;
    }, { timeout: 60 * 60 * 1000 });

    console.log("Playback ended.");

    // 给 ended 事件里的 sendFrontendSummary() 留一点提交时间
    await page.waitForTimeout(3000);

    console.log(`===== Finished: ${videoName}, ${codec}, ${fps} =====`);
}

(async () => {
    const browser = await chromium.launch({
        headless: false
    });

    const page = await browser.newPage();

    page.on("console", msg => {
        console.log("[browser]", msg.text());
    });

    await page.goto(SERVER_URL);

    for (const videoName of videos) {
        for (const codec of codecs) {
            for (const fps of fpsList) {
                try {
                    await runOneTest(page, videoName, codec, fps);
                } catch (error) {
                    console.log(`ERROR in ${videoName}, ${codec}, ${fps}`);
                    console.log(error.message);
                }
            }
        }
    }

    console.log("\nAll tests finished.");
    await browser.close();
})();