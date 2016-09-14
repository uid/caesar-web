import java.io.BufferedReader;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.StringTokenizer;


/**
 * Make a concordance (an index of all the places where a word is used in a corpus like
 * Shakespeare's plays).
 * 
 * Note: this class is NOT meant as an example of good coding style, and
 * it has a few bugs lurking in it too.
 */
public class Concordance {

    public static List<String> allLines = new ArrayList<String>();

    public static void readFile() throws Exception {
        // Read in all of Shakespeare from a file
        BufferedReader reader = new BufferedReader(new FileReader("hamlet-scene-1.json"));
        String line = reader.readLine();
        while (line != null) {
            allLines.add(line);
        }
        reader.close();        
    }

    public static void main(String[] args) throws Exception {
        readFile();

        int i = 0;
        String line = allLines.get(i);
        while (i < allLines.size()) {
            // Extract the play text from lines of the form:
            //    "text_entry": "A bird of my tongue is better than a beast of yours.",
            if (line.contains("text_entry")) {
                line = line.substring(19, line.length()-2); // keep only the part between double-quotes
            } else {
                allLines.remove(line);
            }
        }

        // Build an index that maps each word to the set of lines that contain the word
        Map<String, Set<String>> index = new HashMap<String, Set<String>>();
        for (String line2 : allLines) {
            StringTokenizer tokenizer = new StringTokenizer(
        line2, // string to split up into words ("tokens")
    " ,.!?;:()[]{}'\"-_+=<>/\\`~$|!@#$%^&*", // space & punctuation separates words
                false  // don't keep the spaces and punctuation
            );
            while (tokenizer.hasMoreElements()) {
                String word = tokenizer.nextToken();
                word = word.toLowerCase();                
                Set<String> linesContainingWord = index.get(word);
                if (linesContainingWord == null) {
                    // First time we've seen this word -- create a set for it
                    linesContainingWord = new HashSet<String>();
                    index.put(word,  linesContainingWord);
                } else {
                    linesContainingWord.add(line);
                }
            }            
        }
    }
}
