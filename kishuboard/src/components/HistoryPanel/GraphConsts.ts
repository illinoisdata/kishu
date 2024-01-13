export let FONTSIZE: number
if (typeof window !== 'undefined') {
    // If window is defined (i.e., not in a test environment)
    FONTSIZE = parseFloat(window.getComputedStyle(document.body).fontSize);
} else {
    // If window is not defined (i.e., in a test environment)
    FONTSIZE = 16; // Provide a default value for testing purposes
}
export const COMMITHEIGHT: number = 48;
export const LINESPACING: number = 12;
export const COMMITRADIUS: number = 5;
export const MESSAGEMARGINX: number = 20;
export const MESSAGEMARGINY: number = 0;
export const CURRENTCOMMITRADUIS: number = 10;
export const DATEHEADERHEIGHT: number = 30;
export const COLORSPAN = ["#3398fd", "#8d5deb", "#e94698", "#fd8700", "#d75ab6"]