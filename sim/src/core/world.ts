// Where every caddy is: on a shelf (rack bay or spare slot), in a tray slot, or gone (shipped to RMA).
// Like the SQLite inventory of the Pi app, plus the physical truth the PLC switches read.
import type {Slot} from './spec.ts';
import type {Station} from './layout.ts';

export type Loc = {at: 'shelf'; st: string; i: number} | {at: 'tray'; slot: Slot} | {at: 'gone'};

export class World {
  loc = new Map<number, Loc>();
  /** Tray caddies: offset along Y from the seated-in-tray position (mm). A caddy moves only while its finger holds it. */
  trayY = new Map<number, number>();
  stations: Station[];
  nextId: number;

  constructor(stations: Station[], firstId = 101) {
    this.stations = stations;
    let id = firstId;
    for (const st of stations) {
      if (st.kind === 'rack') st.shelves.forEach((_, i) => this.loc.set(id++, {at: 'shelf', st: st.id, i}));
    }
    this.loc.set(id++, {at: 'shelf', st: 'home', i: 0}); // one good spare in S1
    this.nextId = id;
  }

  station(id: string) {
    return this.stations.find((s) => s.id === id)!;
  }

  get racks() {
    return this.stations.filter((s) => s.kind === 'rack');
  }

  get home() {
    return this.station('home');
  }

  at(st: string, i: number): number | null {
    for (const [id, l] of this.loc) if (l.at === 'shelf' && l.st === st && l.i === i) return id;
    return null;
  }

  tray(slot: Slot): number | null {
    for (const [id, l] of this.loc) if (l.at === 'tray' && l.slot === slot) return id;
    return null;
  }

  where(id: number) {
    return this.loc.get(id);
  }

  /** Human-readable location ("R2 bay 3", "S1", "tray A"). */
  name(l: Loc | undefined) {
    if (!l) return '—';
    if (l.at === 'tray') return `tray ${l.slot}`;
    if (l.at === 'gone') return 'RMA (shipped)';
    return l.st === 'home' ? `S${l.i + 1}` : `${l.st} bay ${l.i + 1}`;
  }

  /** Technician visit: take the RMA caddy out of S2 and put a new spare in S1. */
  restock(): {removed: number | null; added: number | null} {
    const removed = this.at('home', 1);
    if (removed !== null) this.loc.set(removed, {at: 'gone'});
    let added: number | null = null;
    if (this.at('home', 0) === null) {
      added = this.nextId++;
      this.loc.set(added, {at: 'shelf', st: 'home', i: 0});
    }
    return {removed, added};
  }
}
