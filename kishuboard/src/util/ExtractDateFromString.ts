export function extractDateFromString(dateString: string) {
    return dateString.substring(0, 10)
}

export function extractTimeFromString(dataString: string){
    return dataString.substring(10,19)
}

export function formatDate(dateString: string): string {
    const options: Intl.DateTimeFormatOptions = { year: 'numeric', month: 'short', day: 'numeric' };
    // Parse the date as a local date
    const parts = dateString.split('-');
    const year = parseInt(parts[0], 10);
    const month = parseInt(parts[1], 10) - 1; // Month is 0-indexed in JavaScript Date
    const day = parseInt(parts[2], 10);
    const date = new Date(year, month, day);
    return date.toLocaleDateString('en-US', options);
}