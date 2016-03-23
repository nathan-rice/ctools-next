/// <reference path="definitions/numeric.d.ts" />

const quadraticBernsteinMatrix = [
    [1, 0, 0, 0],
    [-3, 3, 0, 0],
    [3, -6, 3, 0],
    [-1, 3, -3, 1]
];

const quadraticBernsteinMatrixTranspose = [
    [1, -3, 3, -1],
    [0, 3, -6, 3],
    [0, 0, 3, -3],
    [0, 0, 0, 1]
];

const linearBernsteinMatrixTranspose = [
    [1, -1],
    [0, 1]
];

// Precomputed factorial values
const fact = [1, 1, 2, 6, 24];

const pow = Math.pow;

export class Point {
    constructor(public x: number, public y: number, public z?: number) {}

    toAugmented2DArray(): number[] {
        return [this.x, this.y, 1];
    }

    to2DArray(): number[] {
        return [this.x, this.y];
    }

    toAugmented3DArray(): number[] {
        return [this.x, this.y, this.z, 1];
    }

    to3DArray(): number[] {
        return [this.x, this.y, this.z];
    }
}

export class BezierSurface {
    interpolationX: number[][];
    interpolationY: number[][];
    interpolationZ: number[][];

    constructor(public controlPoints: Point[][]) {
        this.generateInterpolationMatrices();
    }

    protected generateInterpolationMatrix(points: number[][]) {
        let i, j, p;

        // we need to apply the binomial coefficients to the points
        for (i = points.length; i--;) {
            for (j = points[i].length; j--;) {
                // the binomial coefficient here has been simplified since j will never exceed 1
                points[i][j] = points[i][j] * 12 / fact[i] / fact[3 - i]
            }
        }
        p = numeric.dot(points, linearBernsteinMatrixTranspose);
        p = numeric.dot(quadraticBernsteinMatrix, p);
        return p;
    }

    protected generateInterpolationMatrices() {
        this.interpolationX = this.generateInterpolationMatrix(this.x());
        this.interpolationY = this.generateInterpolationMatrix(this.y());
        this.interpolationZ = this.generateInterpolationMatrix(this.z());
    }

    evaluate(u: number, v: number): number {
        let uArr = [1, u, pow(u, 2), pow(u, 3)], vArr = [1, v];
        return numeric.dot(numeric.dot(uArr, this.interpolationZ), vArr);
    }

    projectToUnitSquare(points: Point[]): number[][] {
        let pointArr = points.map(p => p.toAugmented2DArray());
        return numeric.dot(pointArr, this.generateTransformationMatrix()).map(arr => arr.slice(0, 2));
    }

    generateTransformationMatrix(): number[][] {
        let p0 = this.controlPoints[0][0].to2DArray(),
            p1 = this.controlPoints[0][1].to2DArray(),
            p2 = this.controlPoints[1][0].to2DArray(),
            deltaP0P1 = numeric.sub(p1, p0),
            deltaP0P1norm = numeric.norm2(deltaP0P1),
            deltaP0P2 = numeric.sub(p2, p0),
            deltaP0P2norm = numeric.norm2(deltaP0P2),
            scaleTranslate = [
                [1/deltaP0P1norm, 0, -p0[0] / deltaP0P1norm],
                [0, 1/deltaP0P2norm, -p0[1] / deltaP0P2norm],
                [0, 0, 1]
            ],
            cosTheta = (p2[0] - p0[0]) / deltaP0P2norm,
            sinTheta = (p2[1] - p0[1]) / deltaP0P2norm,
            rotate = [
                [cosTheta, -sinTheta, 0],
                [sinTheta, cosTheta, 0],
                [0, 0, 1]
            ];
            return numeric.dot(scaleTranslate, rotate);
    }

    x(): number[][] {
        return this.controlPoints.map(a => a.map(p => p.x));
    }

    y(): number[][] {
        return this.controlPoints.map(a => a.map(p => p.y));
    }

    z(): number[][] {
        return this.controlPoints.map(a => a.map(p => p.z));
    }
}

export class BicubicBezierSurface extends BezierSurface {
    protected generateInterpolationMatrix(points: number[][]) {
        let i, j, p;

        // we need to apply the binomial coefficients to the points
        for (i = points.length; i--;) {
            for (j = points[i].length; j--;) {
                points[i][j] = points[i][j] * 12 / fact[i] / fact[j] / fact[3 - i] / fact[3 - j]
            }
        }
        p = numeric.dot(points, quadraticBernsteinMatrixTranspose);
        p = numeric.dot(quadraticBernsteinMatrix, p);
        return p;
    }
}