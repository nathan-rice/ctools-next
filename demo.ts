/// <reference path="definitions/numeric.d.ts" />
/// <reference path="definitions/rbush.d.ts" />
/// <reference path="definitions/google.maps.d.ts" />

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
    bounds: number[];

    constructor(public controlPoints: Point[][]) {
        let i, j, minX, maxX, minY, maxY, point;
        for (i = controlPoints.length; i--;) {
            for (j = controlPoints[i].length; j--;) {
                point = controlPoints[i][j];
                if (!minX || point.x < minX) minX = point.x;
                if (!maxX || point.x > maxX) maxX = point.x;
                if (!minY || point.y < minY) minY = point.y;
                if (!maxY || point.y < maxY) maxY = point.y;
            }
        }
        this.bounds = [minX, minY, maxX, maxY];
        this.generateInterpolationMatrices();
    }

    protected generateInterpolationMatrix(points: number[][]) {
        let i = points.length, j = points[0].length, n = i - 1, m = j - 1, mn = m * n, coef, p;

        // we need to apply the binomial coefficients to the points
        for (i = points.length; i--;) {
            // the binomial coefficient here has been simplified since j will never exceed 1
            coef = mn / fact[i] / fact[n - i];
            for (j = points[0].length; j--;) {
                points[i][j] *= coef;
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

    evaluatePoints(points: Point[]) {
        let projected = this.projectToUnitSquare(points);
        return projected.map(p => this.evaluate(p[0], p[1]));
    }

    evaluate(u: number, v: number): number {
        if (u < 0 || u > 1 || v < 0 || v > 1) return 0;
        let vArr = [1, v, pow(v, 2), pow(v, 3)], uArr = [1, u];
        return numeric.dot(numeric.dot(uArr, this.interpolationZ), vArr);
    }

    projectToUnitSquare(points: Point[]): number[][] {
        let pointArr = points.map(p => p.toAugmented2DArray());
        return numeric.dot(pointArr, this.generateTransformationMatrix()).map(arr => arr.slice(0, 2));
    }

    generateTranslationMatrix(): number[][] {
        let p = this.controlPoints[0][0];
        return [
            [1, 0, 0],
            [0, 1, 0],
            [-p.x, -p.y, 1]
        ]
    }

    generateRotationMatrix(): number[][] {
        let p0 = this.controlPoints[0][0],
            p1 = this.controlPoints[1][0],
            adjacent = (p1.x - p0.x),
            opposite = (p1.y - p0.y),
            hypotenuse = numeric.norm2([adjacent, opposite]),
            cosTheta = adjacent / hypotenuse,
            sinTheta = opposite / hypotenuse;
        return [
            [cosTheta, -sinTheta, 0],
            [sinTheta, cosTheta, 0],
            [0, 0, 1]
        ]
    }

    generateTransformationMatrix(): number[][] {
        let last = this.controlPoints[0].length - 1,
            mostDistantPoint = this.controlPoints[1][last].toAugmented2DArray(),
            translate = this.generateTranslationMatrix(),
            rotate = this.generateRotationMatrix(),
            translateRotate = numeric.dot(translate, rotate),
            transformedPoint = numeric.dot(mostDistantPoint, translateRotate),
            scale = [
                [1/transformedPoint[0], 0, 0],
                [0, 1/transformedPoint[1], 0],
                [0, 0, 1]
            ];
            return numeric.dot(translateRotate, scale);
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

export class ModelSource {

    surfaces: BezierSurface[];

    static p0d = 0.858789829499;
    static p1d = 1.25486806631;
    static p1z = 0.004827763527348391;
    static p2d = 3;
    static p2z = 0.0111089965382;

    constructor(p0: Point, p1: Point, public mean: number, public standardDeviation: number, transform?: number[][]) {
        let points = ModelSource.generateSurfaces(p0, p1, standardDeviation), scale;
        if (transform) {
            scale = numeric.det(transform);
            points = points.map(a => a.map(p => ModelSource.transformPoint(p, transform, scale)));
        }
        this.surfaces = [
            new BicubicBezierSurface(points.slice(0, 4).map(a => a.slice(0, 4))),
            new BicubicBezierSurface(points.slice(0, 4).map(a => a.slice(3))),
            new BezierSurface(points.slice(3, 5).map(a => a.slice(0, 4))),
            new BezierSurface(points.slice(3, 5).map(a => a.slice(3))),
            new BicubicBezierSurface(points.slice(4).map(a => a.slice(0, 4))),
            new BicubicBezierSurface(points.slice(4).map(a => a.slice(3)))
        ]
    }

    static transformPoint(p: Point, transform: number[][], scale: number) {
        let transformed = numeric.dot(p.toAugmented2DArray(), transform);
        return new Point(transformed[0], transformed[1], p.z / scale)
    }

    static generateSurfaces(p0: Point, p1: Point, standardDeviation: number) {
        let x0 = p0.x,
            y0 = p0.y,
            x1 = p1.x,
            y1 = p1.y,
            dx = x1 - x0,
            dy = y1 - y0,
            segmentSlope = dy / dx,
            dispersionSlope = - 1 / segmentSlope,
            lateralAlpha = pow(dispersionSlope, 2) + 1,
            longitudinalAlpha = pow(segmentSlope, 2) + 1,
            lateralDx = standardDeviation * Math.sqrt(lateralAlpha),
            lateralDy = dispersionSlope * lateralDx,
            longitudinalDx = standardDeviation * Math.sqrt(longitudinalAlpha),
            longitudinalDy = segmentSlope * longitudinalDx;
            /* Note that this is subtly wrong, it doesn't produce a mesh exactly equivalent to a bivariate normal for
             * bicubic surfaces.  That being said, it should be pretty close and was much easier to produce. */
            return this.generateLongitudinalSurfaceControlPoints(p0, p1, longitudinalDx, longitudinalDy).map(p => {
                return this.generateLateralSurfaceControlPoints(p, lateralDx, lateralDy);
            });
    }

    static generateLongitudinalSurfaceControlPoints(p0: Point, p1: Point, dx: number, dy: number) {
        let x0 = p0.x,
            y0 = p0.y,
            x1 = p0.x,
            y1 = p0.y,
            z = p0.z,
            p0d = this.p0d,
            p1d = this.p1d,
            p1z = this.p1z * z,
            p2d = this.p2d,
            p2z = this.p2z * z;
        return [
            new Point(x0 - p2d * dx, y0 - p2d * dy, p2z),
            new Point(x0 - p1d * dx, y0 - p1d * dy, p1z),
            new Point(x0 - p0d * dx, y0 - p0d * dy, z),
            p0,
            p1,
            new Point(x1 - p0d * dx, y1 - p0d * dy, z),
            new Point(x1 - p1d * dx, y1 - p1d * dy, p1z),
            new Point(x1 - p2d * dx, y1 - p2d * dy, p2z)
        ]
    }

    static generateLateralSurfaceControlPoints(center: Point, dx: number, dy: number) {
        let x = center.x,
            y = center.y,
            z = center.z,
            p0d = this.p0d,
            p1d = this.p1d,
            p1z = this.p1z * z,
            p2d = this.p2d,
            p2z = this.p2z * z;
        return [
            new Point(x - p2d * dx, y - p2d * dy, p2z),
            new Point(x - p1d * dx, y - p1d * dy, p1z),
            new Point(x - p0d * dx, y - p0d * dy, z),
            center,
            new Point(x + p0d * dx, y + p0d * dy, z),
            new Point(x + p1d * dx, y + p1d * dy, p1z),
            new Point(x + p2d * dx, y + p2d * dy, p2z)
        ];
    }
}

export class Viewport {
    public rtree;

    public maxValue: number;

    constructor(public minLat: number, public minLon: number, public maxLat: number, public maxLon: number,
                public xPixels: number, public yPixels: number, pixelRatio: number) {
        let dy = (maxLat - minLat) / (yPixels * pixelRatio),
            dx = (maxLon - minLon) / (xPixels * pixelRatio),
            cells = [];
        for (let i = 0; minLon + i * dx < maxLon; i++) {
            let cellMinLon = minLon + i * dx,
                cellMaxLon = minLon + (i + 1) * dx;
            for (let j = 0; minLat + j * dy < maxLat; j++) {
                let cellMinLat = minLat + i * dy,
                    cellMaxLat = minLat + (i + 0.5) * dy,
                    center = new Point((cellMinLon + cellMaxLon)/2, (cellMinLat + cellMaxLat)/2);
                cells.push([cellMinLon, cellMinLat, cellMaxLon, cellMaxLat, {cell: new ViewportCell(center, i, j)}]);
            }
        }
        this.rtree = rbush(16);
        this.rtree.load(cells);
    }

    protected offset(cell: ViewportCell) {
        return (cell.x + cell.y * this.xPixels) * 4;
    }

    loadSources(sources: ModelSource[]) {
        sources.forEach(source => {
            source.surfaces.forEach(surface => {
                let matches = this.rtree.search(surface.bounds),
                    points = matches.map(match => match.cell.center),
                    values = surface.evaluatePoints(points),
                    maxValue = Math.max(...values),
                    i;
                if (maxValue > this.maxValue) this.maxValue = maxValue;
                for (i = matches.length; i--;) {
                    if (values[i] > 0) matches[i].sources.push({source: source, value: values[i]})
                }
            });
        });
    }

    rasterize(colorMapFunction) {
        let canvas = document.createElement("canvas"),
            context = canvas.getContext("2d", {alpha: true}),
            imageData = new ImageData(this.xPixels, this.yPixels),
            data = imageData.data;
        this.rtree.all().forEach(entry => {
            let offset = this.offset(entry.cell),
                values = colorMapFunction(entry.cell.concentration());
            data[offset++] = values[0];
            data[offset++] = values[1];
            data[offset++] = values[2];
            data[offset] = values[3];
        });
        (context as any).putImageData(imageData, 0, 0);
        return canvas.toDataURL();
    }
}

export class ViewportCell {
    sources: any[];

    constructor(public center: Point, public x: number, public y: number) {}

    concentration(): number {
        return this.sources.reduce((c, s) => c + s.value, 0);
    }
}

export class PollutionOverlay extends google.maps.OverlayView {

    bounds: google.maps.LatLngBounds;
    div: HTMLDivElement;

    constructor(private map: google.maps.Map, private viewport: Viewport) {
        super();
        this.bounds = new google.maps.LatLngBounds(new google.maps.LatLng(viewport.minLat, viewport.minLon),
                                                    new google.maps.LatLng(viewport.maxLat, viewport.maxLon));
        this.setMap(map);
    }

    private createDiv() {
        let div = document.createElement('div');
        div.style.borderStyle = 'none';
        div.style.borderWidth = '0px';
        div.style.position = 'absolute';
        return div;
    }

    private createImg() {
        let img = document.createElement('img');
        // TODO: Add colormap function
        img.src = this.viewport.rasterize(e => e);
        img.style.width = '100%';
        img.style.height = '100%';
        img.style.position = 'absolute';
        return img;
    }

    onAdd() {
        this.div = this.createDiv();
        this.div.appendChild(this.createImg());
        this.getPanes().overlayLayer.appendChild(this.div);
    }

    onRemove() {
        this.div.parentNode.removeChild(this.div);
        this.div = null;
    }

    draw() {
        let projection = this.getProjection(),
            sw = projection.fromLatLngToDivPixel(this.bounds.getSouthWest()),
            ne = projection.fromLatLngToDivPixel(this.bounds.getNorthEast());
        this.div.style.left = sw.x + 'px';
        this.div.style.top = ne.y + 'px';
        this.div.style.width = (ne.x - sw.x) + 'px';
        this.div.style.height = (sw.y - ne.y) + 'px';
    }
}