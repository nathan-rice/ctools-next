declare module numeric {
    export function dot(a: number[], b: number[][]): number[];
    export function dot(a: number[][], b: number[]): number[];
    export function dot(a: number[][], b: number[][]): number[][];
    export function dot(a: number[], b: number[]): number;

    export function transpose(a: number[][]): number[][];

    export function add(a: number[], b: number[]): number[];
    export function add(a: number[][], b: number[][]): number[][];

    export function sub(a: number[], b: number[]): number[];
    export function sub(a: number[][], b: number[][]): number[][];

    export function norm2(a: number[] | number[][]): number;
}