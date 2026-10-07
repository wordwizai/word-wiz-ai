import { test } from "node:test";
import assert from "node:assert/strict";
import { WarmMic } from "./warmMic.ts";

const IDLE_MS = 1000;

// A stand-in device: each open resolves when the test says so.
function fakeDevice() {
  const opens: { resolve: (mic: string) => void; reject: (e: Error) => void; lost: () => void }[] = [];
  const closed: string[] = [];
  const open = (lost: () => void) =>
    new Promise<string>((resolve, reject) => opens.push({ resolve, reject, lost }));
  const close = (mic: string) => {
    closed.push(mic);
  };
  return { opens, closed, mic: new WarmMic<string>(open, close, IDLE_MS) };
}

const flush = () => new Promise((r) => setImmediate(r));

test("a tap during a page-load warm-up shares that open instead of opening twice", async () => {
  const { opens, mic } = fakeDevice();
  void mic.warm();
  const taken = mic.startUsing();
  assert.equal(opens.length, 1);
  opens[0].resolve("mic-1");
  assert.equal(await taken, "mic-1");
  assert.equal(mic.current, "mic-1");
});

test("a later tap reuses the open mic", async () => {
  const { opens, mic } = fakeDevice();
  const first = mic.startUsing();
  opens[0].resolve("mic-1");
  await first;
  mic.stopUsing();
  assert.equal(await mic.startUsing(), "mic-1");
  assert.equal(opens.length, 1);
});

test("closing while a mic is still opening closes it when it arrives", async () => {
  const { opens, closed, mic } = fakeDevice();
  const taken = mic.startUsing();
  mic.close();
  opens[0].resolve("mic-1");
  assert.equal(await taken, null);
  assert.deepEqual(closed, ["mic-1"]);
  assert.equal(mic.current, null);
});

test("an open that arrives after close doesn't clobber a newer open", async () => {
  const { opens, closed, mic } = fakeDevice();
  void mic.warm();
  mic.close();
  const taken = mic.startUsing();
  opens[0].resolve("stale");
  opens[1].resolve("fresh");
  assert.equal(await taken, "fresh");
  assert.deepEqual(closed, ["stale"]);
  assert.equal(mic.current, "fresh");
});

test("a failed open reaches the tap, and the next tap tries again", async () => {
  const { opens, mic } = fakeDevice();
  const taken = mic.startUsing();
  opens[0].reject(new Error("NotAllowedError"));
  await assert.rejects(taken, /NotAllowedError/);
  const retry = mic.startUsing();
  assert.equal(opens.length, 2);
  opens[1].resolve("mic-1");
  assert.equal(await retry, "mic-1");
});

test("warm() swallows a failed open so a page-load attempt can't throw", async () => {
  const { opens, mic } = fakeDevice();
  const warming = mic.warm();
  opens[0].reject(new Error("NotReadableError"));
  await warming;
  assert.equal(mic.current, null);
});

test("an unused mic closes after the idle time, but not during a recording", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  const { opens, closed, mic } = fakeDevice();
  void mic.warm();
  opens[0].resolve("mic-1");
  await flush();

  t.mock.timers.tick(IDLE_MS - 1);
  await mic.startUsing();
  t.mock.timers.tick(IDLE_MS * 5);
  assert.deepEqual(closed, [], "never closed mid-recording");

  mic.stopUsing();
  t.mock.timers.tick(IDLE_MS - 1);
  assert.deepEqual(closed, [], "idle time restarts after each recording");
  t.mock.timers.tick(1);
  assert.deepEqual(closed, ["mic-1"]);
  assert.equal(mic.current, null);
});

test("closeWhenIdle waits for the recording in progress", async () => {
  const { opens, closed, mic } = fakeDevice();
  const taken = mic.startUsing();
  opens[0].resolve("mic-1");
  await taken;
  mic.closeWhenIdle();
  assert.deepEqual(closed, []);
  mic.stopUsing();
  assert.deepEqual(closed, ["mic-1"]);
});

test("closeWhenIdle closes straight away when nothing is recording", async () => {
  const { opens, closed, mic } = fakeDevice();
  void mic.warm();
  opens[0].resolve("mic-1");
  await flush();
  mic.closeWhenIdle();
  assert.deepEqual(closed, ["mic-1"]);
});

test("a lost device is let go, after the recording if one is going", async () => {
  const { opens, closed, mic } = fakeDevice();
  const taken = mic.startUsing();
  opens[0].resolve("mic-1");
  await taken;
  opens[0].lost();
  assert.deepEqual(closed, []);
  mic.stopUsing();
  assert.deepEqual(closed, ["mic-1"]);
  assert.equal(mic.current, null);
});

test("a stale device's late loss doesn't close the current mic", async () => {
  const { opens, closed, mic } = fakeDevice();
  void mic.warm();
  opens[0].resolve("mic-1");
  await flush();
  mic.close();
  void mic.warm();
  opens[1].resolve("mic-2");
  await flush();
  opens[0].lost();
  assert.deepEqual(closed, ["mic-1"]);
  assert.equal(mic.current, "mic-2");
});
