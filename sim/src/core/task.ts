// Cooperative tasks as generators: a task yields a Wait (a predicate) and is resumed in the same sim substep the
// predicate turns true. Unlike promises this is exact at any sim speed and runs headless in Node.

export type Wait = () => boolean;
export type Proc<T = void> = Generator<Wait, T, void>;

export class Fault extends Error {
  code: string;
  constructor(code: string, msg: string) {
    super(msg);
    this.code = code;
  }
}

export class Task {
  private gen: Proc<unknown>;
  private wait: Wait | null = null;
  done = false;

  constructor(gen: Proc<unknown>) {
    this.gen = gen;
  }

  /** Resume the task as long as what it waits for is satisfied. */
  step() {
    for (let i = 0; i < 1000 && !this.done; i++) {
      if (this.wait && !this.wait()) return;
      const r = this.gen.next();
      if (r.done) {
        this.done = true;
        return;
      }
      this.wait = r.value;
    }
  }
}

export const all = (...ws: Wait[]): Wait => () => ws.every((w) => w());

/** Run a Wait as a one-step procedure: `yield* until(w)`. */
export function* until(w: Wait): Proc {
  yield w;
}
