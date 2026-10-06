/**
 * Keeps one microphone open between recordings so a tap records from the
 * first word. Opening a mic from cold takes 0.5-3 s and then fades in over
 * ~0.4 s, and children start reading the moment they tap, so a cold open on
 * every tap lost the start of nearly every attempt.
 *
 * Device-agnostic so the open/close races can be tested without a browser;
 * `M` is whatever `open` produces.
 */
export class WarmMic<M> {
  private readonly openDevice: (onLost: () => void) => Promise<M>;
  private readonly closeDevice: (mic: M) => void;
  private readonly idleMs: number;

  private mic: M | null = null;
  private opening: Promise<M | null> | null = null;
  // Bumped by close(), so an open that finishes afterwards knows it's stale.
  private generation = 0;
  private inUse = false;
  private closeWhenDone = false;
  private idleTimer: ReturnType<typeof setTimeout> | undefined;

  /**
   * @param open Opens the device; calls `onLost` if it later goes away on
   *   its own (unplugged, or taken by the OS).
   * @param idleMs How long an unused mic stays open.
   */
  constructor(
    open: (onLost: () => void) => Promise<M>,
    close: (mic: M) => void,
    idleMs: number,
  ) {
    this.openDevice = open;
    this.closeDevice = close;
    this.idleMs = idleMs;
  }

  get current(): M | null {
    return this.mic;
  }

  /** Opens the mic ahead of a tap. A failure is left for that tap to report. */
  warm(): Promise<void> {
    return this.open().then(
      () => {},
      () => {},
    );
  }

  /** The mic for a recording, opened if need be. Null if closed while opening. */
  async startUsing(): Promise<M | null> {
    this.inUse = true;
    clearTimeout(this.idleTimer);
    try {
      const mic = await this.open();
      if (!mic) this.inUse = false;
      return mic;
    } catch (error) {
      this.inUse = false;
      throw error;
    }
  }

  stopUsing(): void {
    this.inUse = false;
    if (this.closeWhenDone) this.close();
    else if (this.mic) this.armIdleTimer();
  }

  /** Close now, or once the recording in progress ends. */
  closeWhenIdle(): void {
    if (this.inUse) this.closeWhenDone = true;
    else this.close();
  }

  close(): void {
    this.generation++;
    this.opening = null;
    this.closeWhenDone = false;
    clearTimeout(this.idleTimer);
    const mic = this.mic;
    this.mic = null;
    if (mic) this.closeDevice(mic);
  }

  private open(): Promise<M | null> {
    if (this.mic) return Promise.resolve(this.mic);
    if (!this.opening) {
      const generation = this.generation;
      let opened: M | undefined;
      const onLost = () => {
        if (opened !== undefined && this.mic === opened) this.closeWhenIdle();
      };
      this.opening = this.openDevice(onLost).then(
        (mic) => {
          if (generation !== this.generation) {
            this.closeDevice(mic);
            return null;
          }
          opened = mic;
          this.opening = null;
          this.mic = mic;
          if (!this.inUse) this.armIdleTimer();
          return mic;
        },
        (error) => {
          if (generation === this.generation) this.opening = null;
          throw error;
        },
      );
    }
    return this.opening;
  }

  private armIdleTimer() {
    clearTimeout(this.idleTimer);
    this.idleTimer = setTimeout(() => this.closeWhenIdle(), this.idleMs);
  }
}
